import phonenumbers
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from phonenumbers.phonenumberutil import NumberParseException

from . import settings as app_settings

User = get_user_model()


class UsersAuthenticationBackend(ModelBackend):
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
        return None

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
