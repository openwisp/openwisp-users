from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.db.models import Q

User = get_user_model()


class UserAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        users = User.objects.filter(
            Q(email=username) | Q(phone_number=username) | Q(username=username)
        )
        # can not use users.first() because it orders the queryset before
        # returning the first object which is not what we want
        user = users[0] if users else None
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, identifier):
        """
        returns an active user with the identifier supplied
        """
        try:
            # By default, primary key is provided as identifier
            # during login and logout
            return User.objects.get(pk=identifier, is_active=True)
        except (User.DoesNotExist, ValidationError):
            users = User.objects.filter(
                Q(email=identifier)
                | Q(phone_number=identifier)
                | Q(username=identifier)
            ).filter(is_active=True)
            return users[0] if users else None
