from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

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
        return User.objects.filter(
            Q(email=identifier) | Q(phone_number=identifier) | Q(username=identifier)
        )
