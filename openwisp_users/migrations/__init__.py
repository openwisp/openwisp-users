from django.conf import settings

def set_default_organization_uuid(apps, schema_editor):
    """
    Get or create a default organization then 
    set settings._OPENWISP_DEFAULT_ORG_UUID
    """
    organization = apps.get_model('openwisp_users', 'organization')
    default_organization = organization.objects.first()
    if default_organization is None:
        default_organization = organization(
            name='default',
            slug='default',
            description='This is the default organization. '
            'It was created automatically during installation. '
            'You can simply rename it to your organization name.'
        )
        default_organization.full_clean()
        default_organization.save()
    
    # settings._OPENWISP_DEFAULT_ORG_UUID is used in 
    # openwisp-radius.migrations, it helps to enable 
    # users to migrate from freeradius 3
    settings._OPENWISP_DEFAULT_ORG_UUID = default_organization.pk
