import phonenumbers
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone
from phonenumbers.phonenumberutil import NumberParseException

from . import settings as app_settings
from .exceptions import UserPasswordExpired

User = get_user_model()


class BaseBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        queryset = self.get_users(username)
        try:
            # can not use queryset.first() because it orders the queryset
            # by pk before returning the first object which is not what we want
            user = queryset[0]
        except IndexError:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

    def get_users(self, identifier):
        conditions = Q(email=identifier) | Q(username=identifier)
        # if the identifier is a phone number, use the phone number as primary condition
        phone_number = self._get_phone_number(identifier)
        if phone_number:
            conditions = Q(phone_number=phone_number) | conditions
        return User.objects.filter(conditions)

    def _get_phone_number(self, identifier):
        prefixes = [''] + list(app_settings.AUTH_BACKEND_AUTO_PREFIXES)
        for prefix in prefixes:
            value = f'{prefix}{identifier}'
            try:
                phonenumbers.parse(value)
                return value
            except NumberParseException:
                pass
        return False


class UsersAuthenticationBackend(BaseBackend):
    def user_can_authenticate(self, user, raise_exception=False):
        can_authenticate = super().user_can_authenticate(user)
        if user.is_staff or not app_settings.USER_PASSWORD_EXPIRATION:
            return can_authenticate
        today = timezone.now().date()
        password_expiry = user.password_updated + timezone.timedelta(
            days=app_settings.USER_PASSWORD_EXPIRATION
        )
        can_authenticate = (
            can_authenticate and user.has_usable_password() and password_expiry > today
        )
        if not can_authenticate and raise_exception:
            raise UserPasswordExpired(user=user)
        return can_authenticate


class UsersAllowExpiredPassBackend(UsersAuthenticationBackend):
    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user, raise_exception=True)

    def get_user(self, user_id):
        try:
            user = User._default_manager.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if super(BaseBackend, self).user_can_authenticate(user) else None
