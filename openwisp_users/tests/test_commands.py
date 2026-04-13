import csv
from io import StringIO
from unittest.mock import patch

from django.core.files.temp import NamedTemporaryFile
from django.core.management import call_command
from django.test import TestCase
from rest_framework.authtoken.models import Token

from openwisp_utils.tests import capture_stdout

from .. import settings as app_settings
from ..management.commands.export_users import Command, normalize_field
from .utils import TestOrganizationMixin


class TestManagementCommands(TestOrganizationMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.temp_file = NamedTemporaryFile(mode="wt", delete=False)

    def tearDown(self):
        super().tearDown()
        self.temp_file.close()

    def test_export_users(self):
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        user = self._create_user()
        operator = self._create_operator()
        admin = self._create_admin()
        self._create_org_user(organization=org1, user=user, is_admin=True)
        self._create_org_user(organization=org2, user=user, is_admin=False)
        self._create_org_user(organization=org2, user=operator, is_admin=False)
        stdout = StringIO()
        with self.assertNumQueries(2):
            call_command("export_users", filename=self.temp_file.name, stdout=stdout)
        self.assertIn(
            f"User data exported successfully to {self.temp_file.name}",
            stdout.getvalue(),
        )

        # Read the content of the temporary file
        with open(self.temp_file.name, "r") as temp_file:
            csv_reader = csv.reader(temp_file)
            csv_data = list(csv_reader)

        # 3 user and 1 header
        self.assertEqual(len(csv_data), 4)
        expected_headers = [
            normalize_field(f)["name"]
            for f in app_settings.EXPORT_USERS_COMMAND_CONFIG["fields"]
        ]
        self.assertEqual(csv_data[0], expected_headers)
        # Ensuring ordering
        self.assertEqual(csv_data[1][0], str(user.id))
        self.assertEqual(csv_data[2][0], str(operator.id))
        self.assertEqual(csv_data[3][0], str(admin.id))
        # Check organizations formatting
        self.assertEqual(csv_data[1][-1], f"({org1.id},True),({org2.id},False)")
        self.assertEqual(csv_data[2][-1], f"({org2.id},False)")
        self.assertEqual(csv_data[3][-1], "")

    @capture_stdout()
    def test_exclude_fields(self):
        self._create_user()
        call_command(
            "export_users",
            filename=self.temp_file.name,
            exclude_fields=",".join(
                normalize_field(f)["name"]
                for f in app_settings.EXPORT_USERS_COMMAND_CONFIG["fields"][1:]
            ),
        )
        with open(self.temp_file.name, "r") as temp_file:
            csv_reader = csv.reader(temp_file)
            csv_data = list(csv_reader)

        # 1 user and 1 header
        self.assertEqual(len(csv_data), 2)
        self.assertEqual(csv_data[0], ["id"])

    @patch.object(
        app_settings,
        "EXPORT_USERS_COMMAND_CONFIG",
        {
            "fields": ["id", "auth_token.key"],
            "select_related": ["auth_token"],
            "prefetch_related": [],
        },
    )
    def test_related_fields(self):
        user = self._create_user()
        token = Token.objects.create(user=user)
        stdout = StringIO()
        with self.assertNumQueries(1):
            call_command("export_users", filename=self.temp_file.name, stdout=stdout)
        self.assertIn(
            f"User data exported successfully to {self.temp_file.name}",
            stdout.getvalue(),
        )

        # Read the content of the temporary file
        with open(self.temp_file.name, "r") as temp_file:
            csv_reader = csv.reader(temp_file)
            csv_data = list(csv_reader)

        # 3 user and 1 header
        self.assertEqual(len(csv_data), 2)
        expected_headers = [
            normalize_field(f)["name"]
            for f in app_settings.EXPORT_USERS_COMMAND_CONFIG["fields"]
        ]
        self.assertEqual(csv_data[0], expected_headers)
        self.assertEqual(csv_data[1][0], str(user.id))
        self.assertEqual(csv_data[1][1], str(token.key))

    @patch.object(
        app_settings,
        "EXPORT_USERS_COMMAND_CONFIG",
        {
            "fields": ["id", "auth_token.key"],
            "select_related": ["auth_token"],
            "prefetch_related": [],
        },
    )
    @capture_stdout()
    def test_related_fields_no_n_plus_1(self):
        """Query count must not grow with additional users."""
        user1 = self._create_user()
        self._create_operator()
        token1 = Token.objects.create(user=user1)
        # user2 intentionally has no token to cover the ObjectDoesNotExist path
        with self.assertNumQueries(1):
            call_command("export_users", filename=self.temp_file.name)
        with open(self.temp_file.name, "r") as temp_file:
            csv_reader = csv.reader(temp_file)
            csv_data = list(csv_reader)
        # 2 users and 1 header
        self.assertEqual(len(csv_data), 3)
        self.assertEqual(csv_data[1][1], str(token1.key))
        self.assertEqual(csv_data[2][1], "")

    def test_callable_error_handling(self):
        def _broken_callable(user):
            raise ValueError("test error")

        config = {
            "fields": ["id", {"name": "broken", "callable": _broken_callable}],
            "select_related": [],
            "prefetch_related": [],
        }
        self._create_user()
        stderr = StringIO()
        with patch.object(
            app_settings, "EXPORT_USERS_COMMAND_CONFIG", config
        ), self.assertRaises(Exception) as context:
            call_command("export_users", filename=self.temp_file.name, stderr=stderr)
        self.assertIn(
            "Error calling function for field 'broken'", str(context.exception)
        )

    @patch.object(
        app_settings,
        "EXPORT_USERS_COMMAND_CONFIG",
        {
            "fields": [
                "id",
                # single related object with subfields
                {"name": "auth_token", "fields": ["key"]},
                # nullable field
                {"name": "birth_date", "fields": ["year"]},
                # manager with single subfield
                {
                    "name": "openwisp_users_organizationuser",
                    "fields": ["organization_id"],
                },
                # manager with multiple subfields
                {
                    "name": "openwisp_users_organizationuser",
                    "fields": ["organization_id", "is_admin"],
                },
                # dot-notation on a manager
                "openwisp_users_organizationuser.organization_id",
            ],
            "select_related": ["auth_token"],
            "prefetch_related": ["openwisp_users_organizationuser"],
        },
    )
    @capture_stdout()
    def test_subfields_dict_field(self):
        org = self._create_org(name="org1")
        user1 = self._create_user(birth_date=None)
        user2 = self._create_operator(birth_date=None)
        token = Token.objects.create(user=user1)
        self._create_org_user(organization=org, user=user1, is_admin=True)
        # user2 has no token (covers ObjectDoesNotExist)
        # and no org membership (covers empty manager)
        call_command("export_users", filename=self.temp_file.name)
        with open(self.temp_file.name, "r") as temp_file:
            csv_reader = csv.reader(temp_file)
            csv_data = list(csv_reader)
        # 2 users + 1 header
        self.assertEqual(len(csv_data), 3)
        # user1: token present, birth_date None, one org membership
        self.assertEqual(csv_data[1][0], str(user1.id))
        self.assertEqual(csv_data[1][1], str(token.key))  # subfields, single obj
        self.assertEqual(csv_data[1][2], "")  # birth_date is None
        self.assertEqual(csv_data[1][3], str(org.id))  # single-subfield manager
        self.assertEqual(csv_data[1][4], f"(({org.id},True))")  # multi-subfield manager
        self.assertEqual(csv_data[1][5], str(org.id))  # dot-notation manager
        # user2: no token, no org membership
        self.assertEqual(csv_data[2][0], str(user2.id))
        self.assertEqual(csv_data[2][1], "")  # ObjectDoesNotExist auth_token
        self.assertEqual(csv_data[2][2], "")  # birth_date is None
        self.assertEqual(csv_data[2][3], "")  # empty manager
        self.assertEqual(csv_data[2][4], "")  # empty manager
        self.assertEqual(csv_data[2][5], "")  # empty dot-notation manager

    def test_dot_notation_objectdoesnotexist_on_sub_attr(self):
        """Returns empty string when sub-attribute access raises ObjectDoesNotExist."""
        from django.core.exceptions import ObjectDoesNotExist

        class FakeIntermediate:
            @property
            def sub_field(self):
                raise ObjectDoesNotExist

        class FakeUser:
            pk = 1
            intermediate = FakeIntermediate()

        result = Command()._get_field_value(FakeUser(), "intermediate.sub_field")
        self.assertEqual(result, "")
