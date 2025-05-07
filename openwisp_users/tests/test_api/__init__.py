from django.test import TestCase
from django.urls import reverse

from openwisp_users.tests.utils import TestMultitenantAdminMixin


class AuthenticationMixin:
    def _obtain_auth_token(self, username="operator", password="tester"):
        params = {"username": username, "password": password}
        url = reverse("users:user_auth_token")
        response = self.client.post(url, params)
        return response.data["token"]


class TestMultitenantApiMixin(TestMultitenantAdminMixin):
    def _test_access_shared_object(
        self,
        token,
        listview_name=None,
        listview_path=None,
        detailview_name=None,
        detailview_path=None,
        create_payload=None,
        update_payload=None,
        expected_count=0,
        expected_status_codes=None,
    ):
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_payload = create_payload or {}
        update_payload = update_payload or {}
        expected_status_codes = expected_status_codes or {}

        if listview_name or listview_path:
            listview_path = listview_path or reverse(listview_name)
            with self.subTest("HEAD and OPTION methods"):
                response = self.client.head(listview_path, **auth)
                self.assertEqual(response.status_code, expected_status_codes["head"])

                response = self.client.options(listview_path, **auth)
                self.assertEqual(response.status_code, expected_status_codes["option"])

            with self.subTest("Create shared object"):
                response = self.client.post(
                    listview_path,
                    data=create_payload,
                    content_type="application/json",
                    **auth,
                )
                self.assertEqual(response.status_code, expected_status_codes["create"])
                if expected_status_codes["create"] == 400:
                    self.assertEqual(
                        str(response.data["organization"][0]),
                        "This field may not be null.",
                    )

            with self.subTest("List all shared objects"):
                response = self.client.get(listview_path, **auth)
                self.assertEqual(response.status_code, expected_status_codes["list"])
                data = response.data
                if not isinstance(response.data, list):
                    data = data.get("results", data)
                self.assertEqual(len(data), expected_count)

        if detailview_name or detailview_path:
            if not detailview_path and listview_name and expected_count > 0:
                detailview_path = reverse(detailview_name, args=[data[0]["id"]])

            with self.subTest("Retrieve shared object"):
                response = self.client.get(detailview_path, **auth)
                self.assertEqual(
                    response.status_code, expected_status_codes["retrieve"]
                )

            with self.subTest("Update shared object"):
                response = self.client.put(
                    detailview_path,
                    data=update_payload,
                    content_type="application/json",
                    **auth,
                )
                self.assertEqual(response.status_code, expected_status_codes["update"])

            with self.subTest("Delete shared object"):
                response = self.client.delete(detailview_path, **auth)
                self.assertEqual(response.status_code, expected_status_codes["delete"])

    def _test_org_user_access_shared_object(
        self,
        listview_name=None,
        listview_path=None,
        detailview_name=None,
        detailview_path=None,
        create_payload=None,
        update_payload=None,
        expected_count=0,
        expected_status_codes=None,
        token=None,
    ):
        """
        Non-superusers can only view shared objects.
        They cannot create, update, or delete them.
        """
        if not token:
            user = self._create_administrator(organizations=[self._get_org()])
            token = self._obtain_auth_token(user.username, "tester")
        if not expected_status_codes:
            expected_status_codes = {
                "create": 400,
                "list": 200,
                "retrieve": 200,
                "update": 403,
                "delete": 403,
                "head": 200,
                "option": 200,
            }
        self._test_access_shared_object(
            token=token,
            listview_name=listview_name,
            listview_path=listview_path,
            detailview_name=detailview_name,
            detailview_path=detailview_path,
            create_payload=create_payload,
            update_payload=update_payload,
            expected_count=expected_count,
            expected_status_codes=expected_status_codes,
        )

    def _test_superuser_access_shared_object(
        self,
        token,
        listview_path=None,
        listview_name=None,
        detailview_path=None,
        detailview_name=None,
        create_payload=None,
        update_payload=None,
        expected_count=1,
        expected_status_codes=None,
    ):
        """
        Superusers can perform all operations on shared objects.
        """
        if not token:
            user = self._create_admin()
            token = self._obtain_auth_token(user.username, "tester")
        if not expected_status_codes:
            expected_status_codes = {
                "create": 201,
                "list": 200,
                "retrieve": 200,
                "update": 200,
                "delete": 204,
                "head": 200,
                "option": 200,
            }
        self._test_access_shared_object(
            token=token,
            listview_name=listview_name,
            listview_path=listview_path,
            detailview_name=detailview_name,
            detailview_path=detailview_path,
            create_payload=create_payload,
            update_payload=update_payload,
            expected_count=expected_count,
            expected_status_codes=expected_status_codes,
        )


class APITestCase(TestMultitenantApiMixin, AuthenticationMixin, TestCase):
    pass
