from rest_framework.throttling import UserRateThrottle

from openwisp_users import settings as app_settings


class AuthRateThrottle(UserRateThrottle):
    """
    Throttle authentication endpoints by IP for anonymous requests and by user
    for authenticated requests, covering the self-service password-change API.
    """

    rate = app_settings.USERS_AUTH_THROTTLE_RATE

    def get_rate(self):
        """
        Return the dedicated auth rate without consulting DRF defaults.
        """
        return self.rate
