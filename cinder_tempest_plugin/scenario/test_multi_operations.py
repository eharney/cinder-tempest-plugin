#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

from cinder_tempest_plugin.scenario import manager

CONF = config.CONF

class CreateAndAttachManyVolumesTest(manager.ScenarioTest):
    def _create_multiple_resource(self, callback, repeat_count=5,
                                  **kwargs):

        res = []
        for _ in range(repeat_count):
            res.append(callback(**kwargs)['id'])
        return res

    def _wait_for_multiple_resources(self, callback, wait_list, **kwargs):

        for r in wait_list:
            callback(resource_id=r, **kwargs)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(CreateAndAttachManyVolumesTest, cls).setup_credentials()


    def _attach_multiple_volumes(self, res, server):
        """Attach multiple volumes.

           Start attachment process for each volume, then ensure all
           complete after all are already in-flight.  This means that
           attachments happen simultaneously instead of sequentially.
        """
        results = []
        for v in res:
            # start attach process
            att = self.attach_volume_start(server, v)
            results.append(v)

        for v in results:
            # check that attach completed
            self.attach_volume_complete(server, v)

    def _detach_multiple_volumes(self, res, server):
        for v in res:
            # detach volume completely
            # is it worth splitting this in two like attach?
            self._detach_volume(server, v)

    @utils.services('volume', 'compute')
    @decorators.idempotent_id('df8fa9b5-0443-49bb-b652-691d45c0a2f4')
    def test_create_and_attach_many_volumes(self):
        #num_volumes = CONF.num_volumes_to_attach  # TODO
        num_volumes = 3
        # volumes = []

        # start create server
        server = self.create_server()

        kwargs_create = {}

        res = self._create_multiple_resource(self.create_volume,
                                             **kwargs_create,
                                             repeat_count=num_volumes)
        kwargs_wait = {'client': self.volumes_client,
                       'status': 'available'}

        self._wait_for_multiple_resources(
            waiters.wait_for_volume_resource_status,
            res,
            **kwargs_wait)

        # attach all volumes to server
        self._attach_multiple_volumes(res, server)

        # detach all volumes from server
        self._detach_multiple_volumes(res, server)


