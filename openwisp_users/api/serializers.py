from openwisp_utils.api.serializers import ValidatedModelSerializer
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')


class OrganizationSerializer(ValidatedModelSerializer):
    class Meta:
        model = Organization
        fields = (
            'id',
            'name',
            'is_active',
            'slug',
            'description',
            'email',
            'url',
            'created',
            'modified',
        )
