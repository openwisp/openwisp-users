import logging

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from openwisp_utils.api.serializers import ValidatedModelSerializer
from rest_framework import serializers
from swapper import load_model

Group = load_model('openwisp_users', 'Group')
Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
logger = logging.getLogger(__name__)
OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')


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


class CustomPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def display_value(self, instance):
        return instance.user.username

    def get_queryset(self):
        user = self.context['request'].user
        if user.is_superuser:
            queryset = OrganizationUser.objects.all()
        else:
            queryset = OrganizationUser.objects.filter(
                Q(organization__in=user.organizations_managed)
            )
        return queryset


class OrganizationOwnerSerializer(serializers.ModelSerializer):
    organization_user = CustomPrimaryKeyRelatedField(allow_null=True)

    class Meta:
        model = OrganizationOwner
        fields = ('organization_user',)
        extra_kwargs = {'organization_user': {'allow_null': True}}


class OrganizationDetailSerializer(serializers.ModelSerializer):
    owner = OrganizationOwnerSerializer(required=False)

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
            'owner',
            'created',
            'modified',
        )

    def update(self, instance, validated_data):
        if validated_data.get('owner'):
            org_owner = validated_data.pop('owner')
            existing_owner = OrganizationOwner.objects.filter(organization=instance)

            if (
                existing_owner.exists() is False
                and org_owner['organization_user'] is not None
            ):
                org_user = org_owner.get('organization_user')
                with transaction.atomic():
                    org_owner = OrganizationOwner.objects.create(
                        organization=instance, organization_user=org_user
                    )
                    org_owner.full_clean()
                    org_owner.save()
                return super().update(instance, validated_data)

            if existing_owner.exists():
                if org_owner['organization_user'] is None:
                    existing_owner.first().delete()
                    return super().update(instance, validated_data)

                existing_owner_user = existing_owner[0].organization_user
                if org_owner.get('organization_user') != existing_owner_user:
                    org_user = org_owner.get('organization_user')
                    with transaction.atomic():
                        existing_owner.first().delete()
                        org_owner = OrganizationOwner.objects.create(
                            organization=instance, organization_user=org_user
                        )
                        org_owner.full_clean()
                        org_owner.save()

        instance = self.instance or self.Meta.model(**validated_data)
        instance.full_clean()
        return super().update(instance, validated_data)


class MyPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return f'{value.pk}: {value.natural_key()[2]} | {value.name}'

    def to_internal_value(self, value):
        if type(value) is int:
            return value
        return int(value.partition(':')[0])


class GroupSerializer(serializers.ModelSerializer):
    permissions = MyPrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions')

    def create(self, validated_data):
        permissions = validated_data.pop('permissions')
        instance = self.instance or self.Meta.model(**validated_data)
        instance.full_clean()
        instance.save()
        instance.permissions.add(*permissions)
        return instance

    def update(self, instance, validated_data):
        if 'permissions' in validated_data:
            permissions = validated_data.pop('permissions')
            instance.permissions.clear()
            instance.permissions.add(*permissions)
        instance.full_clean()
        return super().update(instance, validated_data)


class OrganizationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = (
            'is_admin',
            'organization',
        )
        extra_kwargs = {
            'organization': {
                'allow_null': True,
                'help_text': _(
                    'If this user is already a member of the selected '
                    'organization, then he/she will be removed from it, '
                    'else the user will become the member of the organization'
                ),
            }
        }


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

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError(_('This field may not be blank.'))
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        org_users = OrganizationUser.objects.filter(user=instance)
        list_of_org_users = []
        for org_user in org_users:
            user = dict()
            user['is_admin'] = org_user.is_admin
            user['organization'] = org_user.organization.id
            list_of_org_users.append(user)
        data['organization_user'] = list_of_org_users
        return data

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

        if org_user_data.get('organization') is not None:
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
            'id',
            'username',
            'password',
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
            'last_login',
            'date_joined',
            'groups',
            'user_permissions',
            'organization_users',
        )
        extra_kwargs = {
            'password': {'read_only': True},
            'last_login': {'read_only': True},
            'date_joined': {'read_only': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        org_users = OrganizationUser.objects.filter(user=instance)
        list_of_org_users = []
        for org_user in org_users:
            user = dict()
            user['is_admin'] = org_user.is_admin
            user['organization'] = org_user.organization.id
            list_of_org_users.append(user)
        data['organization_users'] = list_of_org_users
        return data

    def update(self, instance, validated_data):
        org_user_data = dict()
        if validated_data.get('organization_users'):
            org_user_data = validated_data.pop('organization_users')

        if org_user_data.get('organization') is not None:
            org_user_data['user'] = instance
            org_user_instance = OrganizationUser(**org_user_data)
            if (
                str(org_user_instance.organization.id)
                in instance.organizations_dict.keys()
            ):
                ou = OrganizationUser.objects.get(
                    user=instance, organization=org_user_data['organization']
                )
                ou.delete()
            else:
                org_user_instance.full_clean()
                org_user_instance.save()

        instance = self.instance or self.Meta.model(**validated_data)
        instance.full_clean()
        return super().update(instance, validated_data)


class ChangePasswordSerializer(ValidatedModelSerializer):
    old_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('old_password', 'new_password')


class EmailAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAddress
        fields = ('email', 'verified', 'primary')
