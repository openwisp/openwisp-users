VERSION = (1, 0, 1, 'final')
__version__ = VERSION  # alias

default_app_config = 'openwisp_users.apps.OpenwispUsersConfig'


def get_version():
    version = '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])
    if VERSION[3] != 'final':
        first_letter = VERSION[3][0:1]
        try:
            suffix = VERSION[4]
        except IndexError:
            suffix = 0
        version = '%s%s%s' % (version, first_letter, suffix)
    return version
