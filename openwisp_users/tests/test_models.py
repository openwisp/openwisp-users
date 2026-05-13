from unittest.mock import patch

from allauth.account.models import EmailAddress, get_emailconfirmation_model
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.templatetags.l10n import localize
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now, timedelta
from freezegun import freeze_time
from swapper import load_model

from .. import settings as app_settings
from ..tasks import (
    deactivate_expired_users,
    expiration_reminder_email,
    password_expiration_email,
)
from .utils import TestOrganizationMixin

Organization = load_model("openwisp_users", "Organization")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
OrganizationOwner = load_model("openwisp_users", "OrganizationOwner")
EmailConfirmation = get_emailconfirmation_model()
User = get_user_model()


class TestUsers(TestOrganizationMixin, TestCase):
    user_model = User

    def _assert_email_recipient(self, action, expected):
        with patch("openwisp_users.base.models.send_email") as mock_send:
            action()

        if expected is None:
            mock_send.assert_not_called()
            return

        mock_send.assert_called_once()
        self.assertEqual(
            mock_send.call_args[1]["recipients"],
            [expected],
        )

    def _set_email_states(self, user, states):
        EmailAddress.objects.filter(user=user).delete()
        for state in states:
            state.user = user
            state.save()

    def _setup_deactivation_user(self, label):
        email = f"user{label}@example.com"
        with freeze_time(now() - timedelta(days=5)):
            return self._create_user(
                username=f"testuser{label}",
                email=email,
                is_active=True,
                expiration_date=now().date(),
            )

    def _setup_reminder_user(self, label):
        email = f"user{label}@example.com"
        reminder_days = app_settings.USER_EXPIRATION_WARNING_DAYS

        return self._create_user(
            username=f"testuser{label}",
            email=email,
            expiration_date=now().date() + timedelta(days=reminder_days),
            is_active=True,
        )

    def test_create_superuser_email(self):
        user = User.objects.create_superuser(
            username="tester", password="tester", email="test@superuser.com"
        )
        self.assertEqual(user.emailaddress_set.count(), 1)
        self.assertEqual(user.emailaddress_set.first().email, "test@superuser.com")

    def test_create_superuser_email_empty(self):
        user = User.objects.create_superuser(
            username="tester", password="tester", email=""
        )
        self.assertEqual(user.emailaddress_set.count(), 0)

    def test_unique_email_validation(self):
        self._create_user(username="user1", email="same@gmail.com")
        options = {"username": "user2", "email": "same@gmail.com", "password": "pass1"}
        u = self.user_model(**options)
        with self.assertRaises(ValidationError):
            u.full_clean()

    def test_create_user_without_email(self):
        options = {"username": "testuser", "password": "test1"}
        u = self.user_model(**options)
        u.full_clean()
        u.save()
        self.assertIsNone(u.email)

    def test_organizations_dict(self):
        user = self._create_user(username="organizations_pk")
        self.assertEqual(user.organizations_dict, {})
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        self._create_org(name="org3")
        ou1 = OrganizationUser.objects.create(
            user=user, organization=org1, is_admin=True
        )
        ou2 = OrganizationUser.objects.create(user=user, organization=org2)

        expected = {
            str(org1.pk): {"is_admin": ou1.is_admin, "is_owner": True},
            str(org2.pk): {"is_admin": ou2.is_admin, "is_owner": False},
        }
        self.assertEqual(user.organizations_dict, expected)
        self.assertEqual(len(user.organizations_dict), 2)

        ou2.delete()
        self.assertEqual(len(user.organizations_dict), 1)
        del expected[str(org2.pk)]
        self.assertEqual(user.organizations_dict, expected)

    def test_organizations_dict_cache(self):
        user = self._create_user(username="organizations_pk")
        org1 = self._create_org(name="org1")

        with self.assertNumQueries(1):
            list(user.organizations_dict)

        with self.assertNumQueries(0):
            list(user.organizations_dict)

        OrganizationUser.objects.create(user=user, organization=org1)

        # cache is automatically updated
        with self.assertNumQueries(0):
            list(user.organizations_dict)

    def test_is_member(self):
        user = self._create_user(username="organizations_pk")
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")

        with self.subTest("org instance"):
            self.assertFalse(user.is_member(org1))
            self.assertFalse(user.is_member(org2))
            OrganizationUser.objects.create(user=user, organization=org1)
            self.assertTrue(user.is_member(org1))
            self.assertFalse(user.is_member(org2))

        with self.subTest("org pk"):
            self.assertTrue(user.is_member(org1.pk))
            self.assertFalse(user.is_member(str(org2.pk)))

    def test_is_manager(self):
        user = self._create_user(username="organizations_pk")
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")

        with self.subTest("org instance"):
            self.assertFalse(user.is_manager(org1))
            self.assertFalse(user.is_manager(org2))
            ou = OrganizationUser.objects.create(user=user, organization=org1)
            self.assertFalse(user.is_manager(org1))
            self.assertFalse(user.is_manager(org2))
            ou.is_admin = True
            ou.save()
            self.assertTrue(user.is_manager(org1))
            self.assertFalse(user.is_manager(org2))

        with self.subTest("org pk"):
            self.assertTrue(user.is_manager(org1.pk))
            self.assertFalse(user.is_manager(str(org2.pk)))

    def test_is_owner(self):
        user = self._create_user(username="organizations_pk")
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")

        with self.subTest("org instance"):
            self.assertFalse(user.is_owner(org1))
            self.assertFalse(user.is_owner(org2))
            OrganizationUser.objects.create(user=user, organization=org1, is_admin=True)
            self.assertTrue(user.is_owner(org1))
            self.assertFalse(user.is_owner(org2))

        with self.subTest("org pk"):
            self.assertTrue(user.is_owner(org1.pk))
            self.assertFalse(user.is_owner(str(org2.pk)))

    def test_invalidate_cache_org_owner_user_changed(self):
        org = self._get_org()
        user1 = self._create_user(
            username="user1",
            email="user1@test.org",
        )
        user2 = self._create_user(
            username="user2",
            email="user2@test.org",
        )
        org_user1 = self._create_org_user(user=user1, organization=org, is_admin=True)
        org_user2 = self._create_org_user(user=user2, organization=org, is_admin=True)
        # The first organization admin automatically becomes
        # organization owner.
        self.assertEqual(OrganizationOwner.objects.count(), 1)
        org_owner = OrganizationOwner.objects.first()
        self.assertEqual(org_owner.organization_user, org_user1)
        self.assertEqual(user1.is_owner(org), True)
        org_owner.organization_user = org_user2
        org_owner.full_clean()
        org_owner.save()
        self.assertEqual(org_owner.organization_user, org_user2)
        self.assertEqual(user1.is_owner(org), False)
        self.assertEqual(user2.is_owner(org), True)

    def test_invalidate_cache_org_user_user_changed(self):
        org = self._get_org()
        user1 = self._create_user(
            username="user1",
            email="user1@test.org",
        )
        user2 = self._create_user(
            username="user2",
            email="user2@test.org",
        )
        org_user = self._create_org_user(user=user1, organization=org, is_admin=True)
        self.assertEqual(user1.is_member(org), True)
        self.assertEqual(user2.is_member(org), False)
        org_user.user = user2
        org_user.full_clean()
        org_user.save()
        self.assertEqual(user1.is_member(org), False)
        self.assertEqual(user2.is_member(org), True)

    def test_invalidate_cache_org_status_changed(self):
        org = self._create_org(name="testorg1")
        user1 = self._create_user(username="testuser1", email="user1@test.com")
        self._create_org_user(user=user1, organization=org)
        self.assertEqual(user1.is_member(org), True)
        org.is_active = False
        org.full_clean()
        org.save()
        self.assertEqual(user1.is_member(org), False)

    def test_organizations_managed(self):
        user = self._create_user(username="organizations_pk")
        self.assertEqual(user.organizations_managed, [])
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        org3 = self._create_org(name="org3")
        OrganizationUser.objects.create(user=user, organization=org1, is_admin=True)
        OrganizationUser.objects.create(user=user, organization=org2, is_admin=True)
        OrganizationUser.objects.create(user=user, organization=org3, is_admin=False)
        self.assertEqual(user.organizations_managed, [str(org1.pk), str(org2.pk)])

    def test_organizations_owned(self):
        user = self._create_user(username="organizations_pk")
        self.assertEqual(user.organizations_managed, [])
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        org3 = self._create_org(name="org3")
        OrganizationUser.objects.create(user=user, organization=org1, is_admin=True)
        OrganizationUser.objects.create(user=user, organization=org2, is_admin=True)
        OrganizationUser.objects.create(user=user, organization=org3, is_admin=False)
        self.assertEqual(user.organizations_owned, [str(org1.pk), str(org2.pk)])

    def test_organization_repr(self):
        org = self._create_org(name="org1", is_active=False)
        self.assertIn("disabled", str(org))

    def test_organization_owner_bad_organization(self):
        user = self._create_user(username="user1", email="abc@example.com")
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        org_user = self._create_org_user(organization=org1, user=user)
        org_owner = self._create_org_owner()
        org_owner.organization = org2
        org_owner.organization_user = org_user
        with self.assertRaises(ValidationError):
            org_owner.full_clean()

    def test_create_users_without_email(self):
        options = {"username": "testuser", "password": "test1"}
        u = self.user_model(**options)
        u.full_clean()
        u.save()
        self.assertIsNone(u.email)
        options["username"] = "testuser2"
        u = self.user_model(**options)
        u.full_clean()
        u.save()
        self.assertIsNone(u.email)
        self.assertEqual(User.objects.filter(email=None).count(), 2)

    def test_add_users_with_empty_phone_numbers(self):
        user1 = self.user_model(
            username="user1",
            email="email1@email.com",
            password="user1",
            phone_number="",
        )
        user2 = self.user_model(
            username="user2",
            email="email2@email.com",
            password="user2",
            phone_number="",
        )
        user1.full_clean()
        user2.full_clean()
        user1.save()
        user2.save()
        self.assertIsNone(user1.phone_number)
        self.assertIsNone(user2.phone_number)
        self.assertEqual(self.user_model.objects.filter(phone_number=None).count(), 2)

    def test_user_get_pk(self):
        org = Organization.objects.first()
        pk = str(org.pk)
        with self.subTest("standard tests"):
            self.assertEqual(User._get_pk(org), pk)
            self.assertEqual(User._get_pk(org.pk), pk)
            self.assertEqual(User._get_pk(pk), pk)
        with self.subTest("None case"):
            self.assertEqual(User._get_pk(None), None)
        with self.subTest("ValueError if another type passed"):
            with self.assertRaises(ValueError) as context_manager:
                User._get_pk([])
            self.assertEqual(
                str(context_manager.exception),
                "expected UUID, str or Organization instance",
            )

    def test_orguser_is_admin_change(self):
        org = self._create_org(name="test-org")
        user1 = self._create_user(username="user1", email="user1@email.com")
        user2 = self._create_user(username="user2", email="user2@email.com")
        org_user1 = self._create_org_user(user=user1, organization=org, is_admin=True)
        org_user2 = self._create_org_user(user=user2, organization=org, is_admin=True)

        with self.subTest("change is_admin when org_user belongs to org_owner"):
            msg = (
                f"{user1.username} is the owner of the organization: "
                f"{org}, and cannot be downgraded"
            )
            with self.assertRaisesMessage(ValidationError, msg):
                with self.assertNumQueries(1):
                    org_user1.is_admin = False
                    org_user1.full_clean()

        with self.subTest("change is_admin when org_user doesnot belong to orgowner"):
            org_user2.is_admin = False
            org_user2.full_clean()
            org_user2.save()
            self.assertEqual(org_user2.is_admin, False)

    @override_settings(
        ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL="email_confirmation_success",
        ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL=(
            "email_confirmation_success"
        ),
    )
    def test_email_verification_success(self):
        user = self._create_user()
        user.emailaddress_set.update(verified=False)
        email_address = user.emailaddress_set.first()
        email_confirmation = EmailConfirmation.create(email_address)
        email_confirmation.send()
        url = reverse("account_confirm_email", args=[email_confirmation.key])
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Your email has been verified successfully.")
        self.assertContains(response, "This web page can be closed.")

    @override_settings(ACCOUNT_LOGOUT_REDIRECT_URL="logout_success")
    def test_logout_success(self):
        user = self._create_user()
        self.client.force_login(user)
        response = self.client.post(reverse("account_logout"), follow=True)
        self.assertContains(response, "Logout successful.")
        self.assertContains(response, "This web page can be closed.")

    def test_organization_user_string_representation(self):
        org = self._get_org()
        user = self._create_user()
        org_user = self._create_org_user(
            organization=org,
            user=user,
        )

        with self.subTest("Test user first and last names are mot empty"):
            self.assertEqual(
                str(org_user), f"{user.first_name} {user.last_name} ({org.name})"
            )

        user.first_name = ""
        user.last_name = ""
        user.save()
        org_user.refresh_from_db()

        with self.subTest("Test user first and last names are empty"):
            self.assertEqual(str(org_user), f"{user.username} ({org.name})")

    def test_add_user(self):
        org = self._get_org()
        user = self._create_user()
        org_user = org.add_user(user)
        self.assertIsInstance(org_user, OrganizationUser)
        self.assertTrue(org_user.is_admin)

    def test_has_password_expired(self):
        staff_user = self._create_operator()
        end_user = self._create_user()

        # User.objects.create_user does not call User.set_password.
        # Therefore, we set the password_updated field manually.
        User.objects.update(password_updated=now().date())
        staff_user.refresh_from_db()
        end_user.refresh_from_db()

        with self.subTest("Test password expiration feature disabled"):
            with (
                patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 0),
                patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 0),
            ):
                self.assertEqual(staff_user.has_password_expired(), False)
                self.assertEqual(end_user.has_password_expired(), False)

        with self.subTest("Test password is not expired"):
            with (
                patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 10),
                patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10),
            ):
                self.assertEqual(staff_user.has_password_expired(), False)
                self.assertEqual(end_user.has_password_expired(), False)

        with self.subTest("Test password is expired"):
            User.objects.update(password_updated=now().date() - timedelta(days=180))
            staff_user.refresh_from_db()
            end_user.refresh_from_db()
            with (
                patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 10),
                patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10),
            ):
                self.assertEqual(staff_user.has_password_expired(), True)
                self.assertEqual(end_user.has_password_expired(), True)

        with self.subTest("Test password_updated is None"):
            User.objects.update(password_updated=None)
            end_user.refresh_from_db()
            with (
                patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 10),
                patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10),
            ):
                self.assertEqual(end_user.has_password_expired(), False)

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 90)
    def test_password_expiration_mail(self):
        user_expiry_date = now().date() - timedelta(
            days=(app_settings.USER_PASSWORD_EXPIRATION - 7)
        )
        staff_user_expiry_date = now().date() - timedelta(
            days=(app_settings.STAFF_USER_PASSWORD_EXPIRATION - 7)
        )
        staff_user = self._create_operator()
        end_user = self._create_user()

        with self.subTest(
            "Test end-user and staff user has different expiration dates"
        ):
            User.objects.filter(is_staff=False).update(
                password_updated=user_expiry_date
            )
            User.objects.filter(is_staff=True).update(
                password_updated=staff_user_expiry_date
            )
            password_expiration_email.delay()
            self.assertEqual(len(mail.outbox), 2)
            self.assertEqual(mail.outbox.pop().to, [end_user.email])
            self.assertEqual(mail.outbox.pop().to, [staff_user.email])

        staff_user.delete()

        with self.subTest("Test email is sent to users with verified email"):
            unverified_email_user = self._create_user(
                username="unverified_email",
                email="unverified_email@example.com",
            )
            # Re-using object to make tests run quickly
            verified_email_user = end_user
            EmailAddress.objects.filter(user_id=unverified_email_user.id).update(
                verified=False
            )
            User.objects.filter(is_staff=False).update(
                password_updated=user_expiry_date
            )
            password_expiration_email.delay()
            expected_date = localize((now() + timedelta(days=7)).date())
            self.assertEqual(len(mail.outbox), 1)
            email = mail.outbox.pop()
            self.assertEqual(email.to, [verified_email_user.email])
            self.assertEqual(email.subject, "Action Required: Password Expiry Notice")
            self.assertEqual(
                email.body,
                "We inform you that the password for your account tester will expire"
                f" in 7 days, precisely on {expected_date}.\n\n"
                "Kindly proceed with updating your password by clicking on the"
                " button below.",
            )
            self.assertIn(
                "<p>We inform you that the password for your account tester will expire"
                f" in 7 days, precisely on {expected_date}.<p>\n\n<p>",
                email.alternatives[0][0],
            )
            self.assertIn(
                "Kindly proceed with updating your password by clicking on the button"
                " below.<p>",
                email.alternatives[0][0],
            )
            self.assertNotEqual(email.to, [unverified_email_user.email])

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    @patch("openwisp_users.tasks.sleep")
    def test_password_expiration_mail_sleep(self, mocked_sleep):
        user_expiry_date = now().date() - timedelta(
            days=(app_settings.USER_PASSWORD_EXPIRATION - 7)
        )
        for i in range(10):
            self._create_user(username=f"user{i}", email=f"user{i}@example.com")
        EmailAddress.objects.update(verified=True)
        self.assertEqual(User.objects.count(), 10)
        User.objects.update(password_updated=user_expiry_date)
        password_expiration_email.delay()
        mocked_sleep.assert_called()
        self.assertGreaterEqual(mocked_sleep.call_args[0][0], 1)
        self.assertLessEqual(mocked_sleep.call_args[0][0], 2)

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 0)
    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 0)
    def test_password_expiration_mail_settings_disabled(self):
        """
        Tests that email are not sent when password expiration feature is disabled
        """
        self.assertEqual(app_settings.USER_PASSWORD_EXPIRATION, 0)
        self.assertEqual(app_settings.STAFF_USER_PASSWORD_EXPIRATION, 0)
        self._create_user()
        User.objects.update(password_updated=now().date() - timedelta(days=180))
        with patch("openwisp_users.tasks.send_email") as mocked_send_email:
            password_expiration_email.delay()
        mocked_send_email.assert_not_called()

    def test_expiration_date_validation(self):
        user = self._create_user(username="testuser", email="testuser@example.com")

        with self.subTest("Expiration date in past"):
            user.expiration_date = now().date() - timedelta(days=1)
            with self.assertRaises(ValidationError) as context:
                user.full_clean()
            self.assertIn("expiration_date", context.exception.message_dict)

        with self.subTest("Expiration date is today"):
            user.expiration_date = now().date()
            user.full_clean()
            self.assertEqual(user.expiration_date, now().date())

        with self.subTest("Expiration date in future"):
            future_date = now().date() + timedelta(days=30)
            user.expiration_date = future_date
            user.full_clean()
            self.assertEqual(user.expiration_date, future_date)

        with self.subTest("Expiration date is none"):
            user.expiration_date = None
            user.full_clean()
            self.assertIsNone(user.expiration_date)

    def test_deactivate_expired_users(self):
        with freeze_time(now() - timedelta(days=5)):
            expired_user = self._create_user(
                username="expired",
                email="expired@example.com",
                is_active=True,
                expiration_date=now().date(),
            )
        future_user = self._create_user(
            username="future",
            email="future@example.com",
            is_active=True,
            expiration_date=now().date() + timedelta(days=30),
        )
        none_user = self._create_user(
            username="none",
            email="none@example.com",
            is_active=True,
            expiration_date=None,
        )
        deactivate_expired_users()
        expired_user.refresh_from_db()
        future_user.refresh_from_db()
        none_user.refresh_from_db()
        self.assertFalse(expired_user.is_active)
        self.assertTrue(future_user.is_active)
        self.assertTrue(none_user.is_active)
        self.assertEqual(len(mail.outbox), 1)

    def test_deactivate_expired_users_skips_inactive(self):
        with freeze_time(now() - timedelta(days=5)):
            inactive_user = self._create_user(
                username="inactive",
                email="inactive@example.com",
                is_active=False,
                expiration_date=now().date(),
            )
        with patch("openwisp_users.base.models.send_email") as mock_send:
            deactivate_expired_users()

        inactive_user.refresh_from_db()
        self.assertFalse(inactive_user.is_active)
        mock_send.assert_not_called()

    def test_deactivate_expired_users_idempotent(self):
        with freeze_time(now() - timedelta(days=5)):
            expired_user = self._create_user(
                username="expired",
                email="expired@example.com",
                is_active=True,
                expiration_date=now().date(),
            )
            EmailAddress.objects.filter(user=expired_user).update(verified=True)

        with patch("openwisp_users.base.models.send_email") as mock_send:
            deactivate_expired_users()

            expired_user.refresh_from_db()
            self.assertEqual(expired_user.is_active, False)
            mock_send.assert_called_once()

            mock_send.reset_mock()
            deactivate_expired_users()
            expired_user.refresh_from_db()
            self.assertEqual(expired_user.is_active, False)
            mock_send.assert_not_called()

    def test_deactivate_expired_users_without_expiration_date(self):
        none_user = self._create_user(
            username="none",
            email="none@example.com",
            is_active=True,
            expiration_date=None,
        )
        with patch("openwisp_users.base.models.send_email"):
            deactivate_expired_users()

        none_user.refresh_from_db()
        self.assertTrue(none_user.is_active)

    def test_deactivate_expired_users_sends_email(self):
        with freeze_time(now() - timedelta(days=5)):
            expired_user = self._create_user(
                username="expired",
                email="expired@example.com",
                is_active=True,
                expiration_date=now().date(),
            )
            EmailAddress.objects.filter(user=expired_user).update(verified=True)

        deactivate_expired_users()
        expected_date = localize(expired_user.expiration_date)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [expired_user.email])
        # Verify exact subject and full plain/html bodies
        self.assertEqual(email.subject, "Your account has been deactivated")
        self.assertEqual(
            email.body,
            "We inform you that your account expired has been deactivated because"
            f" it expired on {expected_date}."
            "\n\n\nPlease contact your administrator if you need to reactivate"
            " your account.",
        )
        self.assertInHTML(
            '<div class="msg"><p>'
            "We inform you that your account expired has been deactivated"
            f" because it expired on {expected_date}."
            "</p>"
            "<p>"
            "Please contact your administrator if you need to reactivate your account."
            "</p>",
            email.alternatives[0][0],
        )

    def test_deactivate_expired_users_continues_on_send_failure(self):
        u1 = self._create_user(
            username="u1",
            email="u1@example.com",
            is_active=True,
            expiration_date=now().date(),
        )
        u2 = self._create_user(
            username="u2",
            email="u2@example.com",
            is_active=True,
            expiration_date=now().date(),
        )
        EmailAddress.objects.update(verified=True)
        # First call raises, second succeeds
        side_effects = [Exception("SMTP failure"), None]
        with (
            patch(
                "openwisp_users.base.models.send_email", side_effect=side_effects
            ) as mock_send,
            patch("logging.Logger.exception") as mocked_logger,
        ):
            count = deactivate_expired_users()

        self.assertEqual(count, 2)
        u1.refresh_from_db()
        u2.refresh_from_db()
        self.assertEqual(u1.is_active, False)
        self.assertEqual(u2.is_active, False)
        self.assertEqual(mock_send.call_count, 2)
        mocked_logger.assert_called_once()

    def test_deactivate_expired_users_email_unverified(self):
        with freeze_time(now() - timedelta(days=5)):
            expired_user = self._create_user(
                username="expired",
                email="expired@example.com",
                is_active=True,
                expiration_date=now().date(),
            )
            EmailAddress.objects.filter(user=expired_user).update(verified=False)

        deactivate_expired_users()
        expired_user.refresh_from_db()
        self.assertEqual(expired_user.is_active, False)
        self.assertEqual(len(mail.outbox), 0)

    def test_deactivate_expired_users_recipient_selection(self):
        with self.subTest("verified primary email is used"):
            User.objects.all().delete()
            user = self._setup_deactivation_user("dra")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="primary@dra.com",
                        verified=True,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                deactivate_expired_users,
                "primary@dra.com",
            )

        with self.subTest("primary unverified, verified non-primary used as fallback"):
            User.objects.all().delete()
            user = self._setup_deactivation_user("drb")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="primary@drb.com",
                        verified=False,
                        primary=True,
                    ),
                    EmailAddress(
                        email="verified@drb.com",
                        verified=True,
                        primary=False,
                    ),
                ],
            )
            self._assert_email_recipient(
                deactivate_expired_users,
                "verified@drb.com",
            )

        with self.subTest("no primary, first verified email selected"):
            User.objects.all().delete()
            user = self._setup_deactivation_user("drc")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="first@drc.com",
                        verified=True,
                        primary=False,
                    ),
                    EmailAddress(
                        email="second@drc.com",
                        verified=True,
                        primary=False,
                    ),
                ],
            )
            self._assert_email_recipient(
                deactivate_expired_users,
                "first@drc.com",
            )

        with self.subTest("verified primary preferred over other verified"):
            User.objects.all().delete()
            user = self._setup_deactivation_user("drd")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="nonprimary@drd.com",
                        verified=True,
                        primary=False,
                    ),
                    EmailAddress(
                        email="primary@drd.com",
                        verified=True,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                deactivate_expired_users,
                "primary@drd.com",
            )

        with self.subTest("user.email differs from verified email"):
            User.objects.all().delete()
            user = self._setup_deactivation_user("dre")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="verified@dre.com",
                        verified=True,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                deactivate_expired_users,
                "verified@dre.com",
            )
            self.assertNotEqual(user.email, "verified@dre.com")

        with self.subTest("no verified email skips sending"):
            User.objects.all().delete()
            user = self._setup_deactivation_user("drf")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="unverified@drf.com",
                        verified=False,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                deactivate_expired_users,
                None,
            )

    @patch.object(app_settings, "USER_EXPIRATION_WARNING_DAYS", 7)
    def test_expiration_reminder_email(self):
        reminder_date = now().date() + timedelta(days=7)
        user = self._create_user(
            username="reminder",
            email="reminder@example.com",
            expiration_date=reminder_date,
            is_active=True,
        )
        EmailAddress.objects.filter(user=user).update(verified=True)

        expiration_reminder_email()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [user.email])
        # Verify exact subject and full plain/html bodies
        expected_date = localize(user.expiration_date)
        self.assertEqual(email.subject, "Action Required: Account Expiration Notice")
        self.assertEqual(
            email.body,
            (
                "We inform you that your account "
                f"{user.username} will expire in "
                f"{app_settings.USER_EXPIRATION_WARNING_DAYS} days on "
                f"{expected_date}."
                "\n\n\n"
                "Please contact your administrator if you need to extend your access."
            ),
        )
        self.assertInHTML(
            (
                '<div class="msg"><p>'
                "We inform you that your account "
                f"<strong>{user.username}</strong> will expire in"
                f" {app_settings.USER_EXPIRATION_WARNING_DAYS} days on {expected_date}."
                "</p><p>"
                "Please contact your administrator if you need to extend your access."
                "</p></div>"
            ),
            email.alternatives[0][0],
        )

    @patch.object(app_settings, "USER_EXPIRATION_WARNING_DAYS", 7)
    def test_expiration_reminder_email_continues_on_send_failure(self):
        reminder_date = now().date() + timedelta(days=7)
        self._create_user(
            username="r1",
            email="r1@example.com",
            expiration_date=reminder_date,
            is_active=True,
        )
        self._create_user(
            username="r2",
            email="r2@example.com",
            expiration_date=reminder_date,
            is_active=True,
        )
        EmailAddress.objects.update(verified=True)
        side_effects = [Exception("SMTP down"), None]
        with (
            patch(
                "openwisp_users.base.models.send_email", side_effect=side_effects
            ) as mock_send,
            patch("logging.Logger.exception") as mocked_logger,
        ):
            # Should not raise despite the first call failing
            expiration_reminder_email()

        self.assertEqual(mock_send.call_count, 2)
        mocked_logger.assert_called_once()

    @patch.object(app_settings, "USER_EXPIRATION_WARNING_DAYS", 7)
    def test_expiration_reminder_email_verified_only(self):
        reminder_date = now().date() + timedelta(days=7)
        verified_email_user = self._create_user(
            username="verified",
            email="verified@example.com",
            expiration_date=reminder_date,
            is_active=True,
        )
        verified_email_user.save()
        EmailAddress.objects.filter(user=verified_email_user).update(verified=True)
        unverified_email_user = self._create_user(
            username="unverified",
            email="unverified@example.com",
            expiration_date=reminder_date,
            is_active=True,
        )
        unverified_email_user.save()
        EmailAddress.objects.filter(user=unverified_email_user).update(verified=False)

        expiration_reminder_email()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [verified_email_user.email])

    @patch.object(app_settings, "USER_EXPIRATION_WARNING_DAYS", 7)
    def test_expiration_reminder_email_inactive_user(self):
        reminder_date = now().date() + timedelta(days=7)
        inactive_user = self._create_user(
            username="inactive",
            email="inactive@example.com",
            expiration_date=reminder_date,
            is_active=False,
        )
        EmailAddress.objects.filter(user=inactive_user).update(verified=True)
        expiration_reminder_email()
        self.assertEqual(len(mail.outbox), 0)

    @patch.object(app_settings, "USER_EXPIRATION_WARNING_DAYS", 0)
    def test_expiration_reminder_email_disabled(self):
        reminder_date = now().date() + timedelta(days=7)
        user = self._create_user(
            username="reminder",
            email="reminder@example.com",
            expiration_date=reminder_date,
            is_active=True,
        )
        EmailAddress.objects.filter(user=user).update(verified=True)
        with patch("openwisp_users.base.models.send_email") as mock_send:
            expiration_reminder_email()
            mock_send.assert_not_called()

    @patch.object(app_settings, "USER_EXPIRATION_WARNING_DAYS", 7)
    def test_expiration_reminder_email_recipient_selection(self):
        with self.subTest("verified primary email is used"):
            User.objects.all().delete()
            user = self._setup_reminder_user("era")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="primary@era.com",
                        verified=True,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                expiration_reminder_email,
                "primary@era.com",
            )

        with self.subTest("primary unverified, verified non-primary used as fallback"):
            User.objects.all().delete()
            user = self._setup_reminder_user("erb")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="primary@erb.com",
                        verified=False,
                        primary=True,
                    ),
                    EmailAddress(
                        email="verified@erb.com",
                        verified=True,
                        primary=False,
                    ),
                ],
            )
            self._assert_email_recipient(
                expiration_reminder_email,
                "verified@erb.com",
            )

        with self.subTest("no primary, first verified email selected"):
            User.objects.all().delete()
            user = self._setup_reminder_user("erc")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="first@erc.com",
                        verified=True,
                        primary=False,
                    ),
                    EmailAddress(
                        email="second@erc.com",
                        verified=True,
                        primary=False,
                    ),
                ],
            )
            self._assert_email_recipient(
                expiration_reminder_email,
                "first@erc.com",
            )

        with self.subTest("verified primary preferred over other verified"):
            User.objects.all().delete()
            user = self._setup_reminder_user("erd")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="nonprimary@erd.com",
                        verified=True,
                        primary=False,
                    ),
                    EmailAddress(
                        email="primary@erd.com",
                        verified=True,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                expiration_reminder_email,
                "primary@erd.com",
            )

        with self.subTest("user.email differs from verified email"):
            User.objects.all().delete()
            user = self._setup_reminder_user("ere")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="verified@ere.com",
                        verified=True,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                expiration_reminder_email,
                "verified@ere.com",
            )
            self.assertNotEqual(user.email, "verified@ere.com")

        with self.subTest("no verified email skips sending"):
            User.objects.all().delete()
            user = self._setup_reminder_user("erf")
            self._set_email_states(
                user,
                [
                    EmailAddress(
                        email="unverified@erf.com",
                        verified=False,
                        primary=True,
                    ),
                ],
            )
            self._assert_email_recipient(
                expiration_reminder_email,
                None,
            )
