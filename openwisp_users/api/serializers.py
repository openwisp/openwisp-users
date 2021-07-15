from django.contrib.auth import get_user_model
from openwisp_utils.api.serializers import ValidatedModelSerializer
from rest_framework import serializers
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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'phone_number',
            'birth_date',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
        )
        read_only_fields = ('last_login', 'date_joined')
        extra_kwargs = {'email': {'required': True}}

    def create(self, validated_data):
        group_data = validated_data.pop('groups', None)
        instance = self.instance or self.Meta.model(**validated_data)
        password = validated_data.pop('password')
        instance.set_password(password)
        instance.full_clean()
        instance.save()
        if group_data:
            instance.groups.add(*group_data)
        return instance
