from django.contrib.auth.models import Permission
from ..models import Organization, User, OrganizationUser


class TestOrganizationMixin(object):
    def _create_user(self, **kwargs):
        opts = dict(username='tester',
                    password='tester',
                    first_name='Tester',
                    last_name='Tester',
                    email='test@tester.com')
        opts.update(kwargs)
        user = User.objects.create_user(**opts)
        return user

    def _create_admin(self, **kwargs):
        opts = dict(username='admin',
                    email='admin@admin.com',
                    is_superuser=True,
                    is_staff=True)
        opts.update(kwargs)
        return self._create_user(**opts)

    def _create_org(self, **kwargs):
        options = {
            'name': 'test org',
            'is_active': True,
            'slug': 'test-org'
        }
        options.update(kwargs)
        org = Organization.objects.create(**options)
        return org

    def _create_operator(self):
        operator = User.objects.create_user(username='operator',
                                            password='tester',
                                            email='operator@test.com',
                                            is_staff=True)
        operator.user_permissions.add(
            *Permission.objects.filter(codename__endswith='user'))
        return operator

    def _get_org(self):
        try:
            return Organization.objects.get(name="test org")
        except Organization.DoesNotExist:
            return self._create_org()

    def _get_operator(self):
        try:
            return User.objects.get(username="operator")
        except User.DoesNotExist:
            return self._create_operator()

    def _create_org_user(self, **kwargs):
        options = {
            'organization': self._get_org(),
            'is_admin': True,
            'user': self._get_operator()
        }
        options.update(kwargs)
        org = OrganizationUser.objects.create(**options)
        return org
