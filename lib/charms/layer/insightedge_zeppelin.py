import os
import shutil

from charmhelpers.core import host, hookenv
from charmhelpers import fetch
from jujubigdata import utils

from charms.layer.apache_zeppelin import Zeppelin


class IEZeppelin(Zeppelin):
    def install(self):
        """
        Override install to handle nested zeppelin dir, and different
        resource name.
        """
        filename = hookenv.resource_get('insightedge')
        destination = self.dist_config.path('insightedge')

        if not filename:
            return False  # failed to fetch

        extracted = fetch.install_remote('file://' + filename)
        # get the nested dir
        extracted = os.path.join(extracted, os.listdir(extracted)[0])
        if os.path.exists(destination):
            shutil.rmtree(destination)
        shutil.copytree(extracted, destination)

        host.chownr(destination, 'ubuntu', 'root')
        zd = self.dist_config.path('zeppelin') / 'bin' / 'zeppelin-daemon.sh'
        zd.chmod('a+x')

        self.dist_config.add_dirs()
        self.dist_config.add_packages()
        return True

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
