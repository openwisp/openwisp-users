import logging

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from openwisp_utils.api.serializers import ValidatedModelSerializer
from rest_framework import serializers
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
logger = logging.getLogger(__name__)


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


class OrganizationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = (
            'is_admin',
            'organization',
        )


class SuperUserListSerializer(serializers.ModelSerializer):
    organization_user = OrganizationUserSerializer(required=False)

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
            'organization_user',
        )
        read_only_fields = ('last_login', 'date_joined')
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
        }

    def create(self, validated_data):
        group_data = validated_data.pop('groups', None)
        org_user_data = validated_data.pop('organization_user', None)

        instance = self.instance or self.Meta.model(**validated_data)
        password = validated_data.pop('password')
        instance.set_password(password)
        instance.full_clean()
        instance.save()

        if group_data:
            instance.groups.add(*group_data)

        if org_user_data:
            org_user_data['user'] = instance
            org_user_instance = OrganizationUser(**org_user_data)
            org_user_instance.full_clean()
            org_user_instance.save()

        if instance.email:
            try:
                EmailAddress.objects.add_email(
                    self.context['request'],
                    user=instance,
                    email=instance.email,
                    confirm=True,
                    signup=True,
                )
            except Exception as e:
                logger.exception(
                    'Got exception {} while sending '
                    'verification email to user {}, email {}'.format(
                        type(e), instance.username, instance.email
                    )
                )

        return instance


class SuperUserDetailSerializer(serializers.ModelSerializer):
    organization_users = OrganizationUserSerializer(required=False)

    class Meta:
        model = User
        fields = (
            'username',
            'password',  # read_only
            'first_name',
            'last_name',
            'email',
            'bio',
            'url',
            'company',
            'location',
            'phone_number',
            'birth_date',
            'notes',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
            'last_login',
            'date_joined',
            'organization_users',  # Will have to nest this sepparately
        )
        extra_kwargs = {
            'password': {'read_only': True},
            'last_login': {'read_only': True},
            'date_joined': {'read_only': True},
        }
