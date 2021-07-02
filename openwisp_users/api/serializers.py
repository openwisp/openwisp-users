from django.contrib.auth import get_user_model
from openwisp_utils.api.serializers import ValidatedModelSerializer
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()


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


class UserSerializer(ValidatedModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
