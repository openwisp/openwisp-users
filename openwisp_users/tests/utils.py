from ..models import Organization, User


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
