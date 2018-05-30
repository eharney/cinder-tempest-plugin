from tempest.common import utils
from tempest.common import waiters
import tempest.config
import tempest.scenario.manager
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = tempest.config.CONF

class TestEncryptedVolumeToFromImage(tempest.scenario.manager.EncryptionScenarioTest):

    def upload_volume(self, volume):
        image_name = data_utils.rand_name(self.__class__.__name__ + '-Image')

        body = self.volumes_client.upload_volume(volume['id'],
                image_name=image_name,
                disk_format=CONF.volume.disk_format)['os-volume_upload_image']
        image_id = body['image_id']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.compute_images_client.delete_image,
                        image_id)
        waiters.wait_for_image_status(self.compute_images_client, image_id, 'ACTIVE')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                self.volume['id'],
                'available')

        return image_id

    def launch_instance(self):
        image = self.glance_image_create()
        keypair = self.create_keypair()

        return self.create_server(image_id=image, key_name=keypair['name'])



    @classmethod
    def skip_checks(cls):
        super(TestEncryptedVolumeToFromImage, cls).skip_checks()
        if not CONF.compute_feature_enabled.attach_encrypted_volume:
            raise cls.SkipException('Encrypted volume attach is not supported')


    @decorators.idempotent_id('2c4efd50-dc45-4f78-9be1-f522f499209f')
    #@decorators.attr('slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_volume_upload_download(self):
        server = self.launch_instance()

        volume = self.create_encrypted_volume('nova.volume.encryptors.'
                                              'luks.LuksEncryptor',
                                              volume_type='luks')

        attached_volume = self.nova_volume_attach(server, volume)
        self.nova_volume_detach(server, attached_volume)

        # Upload volume to image
        image_id = self.upload_volume(volume)

        # Create image from volume
        new_volume = self.create_volume(imageRef=image_id, volume_type='luks')

        waiters.wait_for_volume_resource_status(self.volumes_client,
                new_volume['id'],
                'available')
