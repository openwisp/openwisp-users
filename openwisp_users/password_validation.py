from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PasswordReuseValidator:
    """
    Django password validator class that does not allow re-using
    user's current password.
    """

    def validate(self, password, user=None):
        if user is None:
            return
        if check_password(password, user.password):
            # The new password is same as the current password
            raise ValidationError(
                _("You cannot re-use your current password. Enter a new password.")
            )

    def get_help_text(self):
        return _("Your password cannot be the same as your current password.")
