from path import Path

from charmhelpers.core import host, hookenv
from charmhelpers import fetch
from jujubigdata import utils

from charms.layer.apache_zeppelin import Zeppelin, ZeppelinAPI


class IEZeppelin(Zeppelin):
    def install(self, force=False):
        """
        Override install to handle nested zeppelin dir, and different
        resource name.
        """
        filename = hookenv.resource_get('insightedge')
        destination = self.dist_config.path('insightedge')

        if not filename:
            return False  # failed to fetch

        if destination.exists() and not force:
            return True

        destination.rmtree_p()  # if reinstalling
        extracted = Path(fetch.install_remote('file://' + filename))
        extracted.dirs()[0].copytree(destination)  # only copy nested dir

        host.chownr(destination, 'ubuntu', 'root')
        zd = self.dist_config.path('zeppelin') / 'bin' / 'zeppelin-daemon.sh'
        zd.chmod('a+x')

        self.dist_config.add_dirs()
        self.dist_config.add_packages()
        return True

    def setup_zeppelin_tutorial(self):
        pass  # this is already done by insightedge

    def update_master(self, master_url, master_ip):
        api = ZeppelinAPI()
        api.modify_interpreter('spark', properties={
            'master': master_url,
            'insightedge.locator': '{}:4174'.format(master_ip),
        })
        self.restart()

    def start(self):
        """
        Override start to use InsightEdge's wrapper.
        """
        # Start if we're not already running. We currently dont have any
        # runtime config options, so no need to restart when hooks fire.
        if not utils.jps("zeppelin"):
            ie_home = self.dist_config.path('insightedge')
            zeppelin_home = self.dist_config.path('zeppelin')
            # chdir here because things like zepp tutorial think ZEPPELIN_HOME
            # is wherever the daemon was started from.
            with host.chdir(zeppelin_home):
                utils.run_as('ubuntu',
                             '{}/sbin/start-zeppelin.sh'.format(ie_home))
            # wait up to 30s for API to start, lest requests fail
            self.wait_for_api(30)

    def stop(self):
        """
        Override start to use InsightEdge's wrapper.
        """
        # Start if we're not already running. We currently dont have any
        # runtime config options, so no need to restart when hooks fire.
        if not utils.jps("zeppelin"):
            ie_home = self.dist_config.path('insightedge')
            zeppelin_home = self.dist_config.path('zeppelin')
            # chdir here because things like zepp tutorial think ZEPPELIN_HOME
            # is wherever the daemon was started from.
            with host.chdir(zeppelin_home):
                utils.run_as('ubuntu',
                             '{}/sbin/stop-zeppelin.sh'.format(ie_home))
            # wait for the process to stop, since issuing a start while the
            # process is still running (i.e., restart) could cause it to not
            # start up again
            self.wait_for_stop(30)
