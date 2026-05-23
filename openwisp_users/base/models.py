import logging
import uuid
from smtplib import SMTPException

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import AbstractUser as BaseUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import OuterRef, Subquery
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.functional import cached_property
from django.utils.timezone import localdate, timedelta
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from swapper import load_model

from openwisp_utils.admin_theme.email import send_email

from .. import settings as app_settings
from ..utils import throttle_email_batch

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    def _create_user(self, *args, **kwargs):
        """
        adds automatic email address object creation to django
        management commands "create_user" and "create_superuser"
        """
        user = super()._create_user(*args, **kwargs)
        self._create_email(user)
        return user

    def _create_email(self, user):
        """
        creates verified and primary email address objects
        """
        if user.email:
            set_primary = (
                EmailAddress.objects.filter(user=user, primary=True).count() == 0
            )
            email = EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
            if set_primary:
                email.set_as_primary()


class AbstractUser(BaseUser):
    """
    OpenWISP User model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, blank=True, null=True)
    bio = models.TextField(_("bio"), blank=True)
    url = models.URLField(_("URL"), blank=True)
    company = models.CharField(_("company"), max_length=30, blank=True)
    location = models.CharField(_("location"), max_length=256, blank=True)
    phone_number = PhoneNumberField(
        _("phone number"), unique=True, blank=True, null=True
    )
    birth_date = models.DateField(_("birth date"), blank=True, null=True)
    notes = models.TextField(
        _("notes"), help_text=_("notes for internal usage"), blank=True
    )
    language = models.CharField(
        max_length=8,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    password_updated = models.DateField(_("password updated"), blank=True, null=True)
    expiration_date = models.DateField(
        _("expiration date"),
        blank=True,
        null=True,
        help_text=_(
            "If set, the account will be deactivated on this date and the user "
            "will no longer be able to log in."
        ),
    )

    objects = UserManager()

    class Meta(BaseUser.Meta):
        abstract = True
        indexes = [
            models.Index(fields=["id", "email"], name="user_id_email_idx"),
            models.Index(
                fields=["is_active", "expiration_date"],
                name="user_active_expiry_idx",
            ),
        ]

    @staticmethod
    def _get_pk(obj):
        """meant for internal usage only"""
        if isinstance(obj, (uuid.UUID, str)):
            pk = obj
        elif isinstance(obj, BaseOrganization):
            pk = obj.pk
        elif obj is None:
            return None
        else:
            raise ValueError("expected UUID, str or Organization instance")
        return str(pk)

    def set_password(self, *args, **kwargs):
        self.password_updated = timezone.now().date()
        return super().set_password(*args, **kwargs)

    def has_password_expired(self):
        if not self.has_usable_password() or self.password_updated is None:
            return False
        if self.is_staff and app_settings.STAFF_USER_PASSWORD_EXPIRATION:
            expiry_date = self.password_updated + timezone.timedelta(
                days=app_settings.STAFF_USER_PASSWORD_EXPIRATION
            )
        elif app_settings.USER_PASSWORD_EXPIRATION:
            expiry_date = self.password_updated + timezone.timedelta(
                days=app_settings.USER_PASSWORD_EXPIRATION
            )
        else:
            return False
        return expiry_date < timezone.now().date()

    def is_member(self, organization):
        return self._get_pk(organization) in self.organizations_dict

    def is_manager(self, organization):
        org_dict = self.organizations_dict.get(self._get_pk(organization))
        return org_dict is not None and (org_dict["is_admin"] or org_dict["is_owner"])

    def is_owner(self, organization):
        org_dict = self.organizations_dict.get(self._get_pk(organization))
        return org_dict is not None and org_dict["is_owner"]

    @cached_property
    def is_owner_of_any_organization(self):
        for value in self.organizations_dict.values():
            if value["is_owner"]:
                return True
        return False

    @property
    def organizations_dict(self):
        """
        Returns a dictionary which represents the organizations which
        the user is member of, or which the user manages or owns.
        """
        cache_key = "user_{}_organizations".format(self.pk)
        organizations = cache.get(cache_key)
        if organizations is not None:
            return organizations

        manager = load_model("openwisp_users", "OrganizationUser").objects
        org_users = manager.filter(
            user=self, organization__is_active=True
        ).select_related("organization", "organizationowner")

        organizations = {}
        for org_user in org_users:
            org = org_user.organization
            org_id = str(org.pk)
            organizations[org_id] = {
                "is_admin": org_user.is_admin,
                "is_owner": hasattr(org_user, "organizationowner"),
            }

        cache.set(cache_key, organizations, 86400 * 2)  # Cache for two days
        return organizations

    def __get_orgs(self, attribute):
        org_list = []
        for org_pk, options in self.organizations_dict.items():
            if options[attribute]:
                org_list.append(org_pk)
        return org_list

    @cached_property
    def organizations_managed(self):
        return self.__get_orgs("is_admin")

    @cached_property
    def organizations_owned(self):
        return self.__get_orgs("is_owner")

    def clean(self):
        if self.email == "":
            self.email = None
        if self.phone_number == "":
            self.phone_number = None
        if (
            self.email
            and self._meta.model.objects.filter(email__iexact=self.email)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {"email": _("User with this Email address already exists.")}
            )
        self._validate_expiration()

    def _validate_expiration(self):
        """
        * Prevent setting the expiration date in the past
        * Prevent reactivating users with an expired date
          (requires setting a new date or clearing it)
        """
        if not self.expiration_date:
            return
        today = localdate()
        is_past_expiration = self.expiration_date < today
        is_expired = self.expiration_date <= today
        previous_state = None
        needs_previous_state = not self._state.adding and (
            is_past_expiration or (self.is_active and is_expired)
        )
        if needs_previous_state:
            previous_state = (
                self._meta.model.objects.filter(pk=self.pk)
                .only("is_active", "expiration_date")
                .first()
            )
        # Prevent setting a past expiration date, but allow keeping an
        # already expired date unchanged while updating other fields.
        if is_past_expiration:
            db_expiration_date = None
            if previous_state:
                db_expiration_date = previous_state.expiration_date
            if self._state.adding or db_expiration_date != self.expiration_date:
                raise ValidationError(
                    {"expiration_date": _("Expiration date cannot be in the past.")}
                )
        if (
            previous_state
            and not previous_state.is_active
            and self.is_active
            and is_expired
        ):
            raise ValidationError(
                {
                    "is_active": _(
                        "Cannot activate an expired account. Clear or extend the"
                        " expiration date first."
                    )
                }
            )

    def _invalidate_user_organizations_dict(self):
        """
        Invalidate the organizations cache of the user
        """
        cache.delete(f"user_{self.pk}_organizations")
        try:
            del self.organizations_managed
        except AttributeError:
            pass
        try:
            del self.organizations_owned
        except AttributeError:
            pass

    @classmethod
    def deactivate_expired_users(cls):
        """
        Deactivate users whose expiration_date is today or earlier.

        Selected rows are locked with ``select_for_update`` inside an atomic
        block so concurrent runs (or admin edits) cannot race with the
        per-user save. Each user is saved individually with
        ``update_fields=["is_active"]`` so post-save hooks still fire for
        consumers that rely on them. Returns the number of users deactivated.

        Emails are sent (outside the transaction) only to affected users
        with a verified email address; all expired active users are
        deactivated regardless of verification status.
        """
        expiry_date = localdate()
        deactivated_user_ids = []
        with transaction.atomic():
            users_to_deactivate = (
                cls.objects.filter(
                    is_active=True,
                    expiration_date__lte=expiry_date,
                )
                .only("id")
                .select_for_update()
            )
            for user in users_to_deactivate.iterator():
                user.is_active = False
                user.save(update_fields=["is_active"])
                deactivated_user_ids.append(user.pk)

        if not deactivated_user_ids:
            return 0

        count = len(deactivated_user_ids)
        users = (
            cls.objects.filter(
                id__in=deactivated_user_ids,
                emailaddress__verified=True,
            )
            .annotate(
                verified_email=Subquery(cls._verified_email_subquery()),
            )
            .distinct()
            .only(
                "id",
                "email",
                "username",
                "language",
                "expiration_date",
            )
            .iterator()
        )
        email_count = 0
        for user in users:
            with translation.override(user.language):
                try:
                    send_email(
                        subject=_("Your account has been deactivated"),
                        body_text=render_to_string(
                            "account/email/account_expired_message.txt",
                            context={
                                "username": user.username,
                                "expiration_date": user.expiration_date,
                            },
                        ).strip(),
                        body_html=render_to_string(
                            "account/email/account_expired_message.html",
                            context={
                                "username": user.username,
                                "expiration_date": user.expiration_date,
                            },
                        ).strip(),
                        recipients=[user.verified_email],
                    )
                except (SMTPException, ConnectionError, OSError):
                    logger.exception(
                        "Error sending deactivation email to user %s",
                        getattr(user, "pk", None),
                    )
            email_count += 1
            throttle_email_batch(email_count)

        return count

    @staticmethod
    def _verified_email_subquery():
        return (
            EmailAddress.objects.filter(
                user=OuterRef("pk"),
                verified=True,
            )
            .order_by("-primary", "id")
            .values("email")[:1]
        )

    @classmethod
    def expiration_reminder_email(cls):
        """
        Send reminder emails to users whose accounts will expire soon.

        This method checks for active users with a verified email whose
        expiration_date equals today + USER_EXPIRATION_WARNING_DAYS and
        sends a localized reminder email.

        Only users with a verified email address receive reminders.
        """
        reminder_days = app_settings.USER_EXPIRATION_WARNING_DAYS
        if reminder_days <= 0:
            return 0

        reminder_date = localdate() + timedelta(days=reminder_days)
        qs = (
            cls.objects.filter(
                is_active=True,
                expiration_date=reminder_date,
                emailaddress__verified=True,
            )
            .annotate(
                verified_email=Subquery(cls._verified_email_subquery()),
            )
            .distinct()
            .only(
                "id",
                "email",
                "username",
                "language",
                "expiration_date",
            )
        )
        count = qs.count()
        email_count = 0
        for user in qs.iterator():
            with translation.override(user.language):
                try:
                    send_email(
                        subject=_("Action Required: Account Expiration Notice"),
                        body_text=render_to_string(
                            "account/email/account_expiration_reminder_message.txt",
                            context={
                                "username": user.username,
                                "expiration_date": user.expiration_date,
                                "days_remaining": reminder_days,
                            },
                        ).strip(),
                        body_html=render_to_string(
                            "account/email/account_expiration_reminder_message.html",
                            context={
                                "username": user.username,
                                "expiration_date": user.expiration_date,
                                "days_remaining": reminder_days,
                            },
                        ).strip(),
                        recipients=[user.verified_email],
                    )
                except (SMTPException, ConnectionError, OSError):
                    logger.exception(
                        "Error sending expiration reminder email to user %s",
                        getattr(user, "pk", None),
                    )
            email_count += 1
            throttle_email_batch(email_count)

        return count


class BaseGroup(object):
    """
    Proxy model used to move ``GroupAdmin``
    under the same app label as the other models
    """

    class Meta:
        proxy = True
        verbose_name = _("group")
        verbose_name_plural = _("groups")


class BaseOrganization(models.Model):
    """
    OpenWISP Organization model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(_("description"), blank=True)
    email = models.EmailField(_("email"), blank=True)
    url = models.URLField(_("URL"), blank=True)

    def __str__(self):
        value = self.name
        if not self.is_active:
            value = "{0} ({1})".format(value, _("disabled"))
        return value

    class Meta:
        abstract = True

    def add_user(self, user, is_admin=False, **kwargs):
        """
        We override this method from the upstream dependency to
        skip the creation of the organization owner, which we perform
        automatically via a signal receiver.
        Without this change, the add_user method would throw IntegrityError.
        """

        if not self.users.all().exists():
            is_admin = True

        OrganizationUser = load_model("openwisp_users", "OrganizationUser")
        return OrganizationUser.objects.create(
            user=user, organization=self, is_admin=is_admin
        )


class BaseOrganizationUser(models.Model):
    """
    OpenWISP OrganizationUser model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

    def clean(self):
        if (
            not self._state.adding
            and self.user.is_owner(self.organization_id)
            and not self.is_admin
        ):
            raise ValidationError(
                _(
                    f"{self.user.username} is the owner of the organization: "
                    f"{self.organization}, and cannot be downgraded"
                )
            )

    @property
    def name(self):
        """
        Returns the connected user's full name or user's username if
        full name method is unavailable (e.g. on a custom user class)
        or if full name is an empty string.
        """
        return self.user.get_full_name() or str(self.user.username)


class BaseOrganizationOwner(models.Model):
    """
    OpenWISP OrganizationOwner model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def clean(self):
        if self.organization_user.organization.pk != self.organization.pk:
            raise ValidationError(
                {
                    "organization_user": _(
                        "The selected user is not member of this organization."
                    )
                }
            )

    class Meta:
        abstract = True
