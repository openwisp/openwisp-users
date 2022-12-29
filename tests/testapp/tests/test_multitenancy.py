from django.test import TestCase
from django.urls import reverse

from ..models import Book, Shelf
from .mixins import TestMultitenancyMixin


class TestMultitenancy(TestMultitenancyMixin, TestCase):
    book_model = Book
    shelf_model = Shelf

    def _create_multitenancy_test_env(self):
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        inactive = self._create_org(name='inactive-org', is_active=False)
        operator = self._create_operator(
            organizations=[org1, inactive],
        )
        administrator = self._create_administrator(
            organizations=[org1, inactive],
        )
        s1 = self._create_shelf(name='shell1', organization=org1)
        s2 = self._create_shelf(name='shell2', organization=org2)
        s3 = self._create_shelf(name='shell3', organization=inactive)
        b1 = self._create_book(name='book1', organization=org1, shelf=s1)
        b2 = self._create_book(name='book2', organization=org2, shelf=s2)
        b3 = self._create_book(name='book3', organization=inactive, shelf=s3)
        data = dict(
            s1=s1,
            s2=s2,
            s3_inactive=s3,
            b1=b1,
            b2=b2,
            b3_inactive=b3,
            org1=org1,
            org2=org2,
            inactive=inactive,
            operator=operator,
            administrator=administrator,
        )
        return data

    def test_shelf_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse('admin:testapp_shelf_changelist'),
            visible=[data['s1'].name, data['org1'].name],
            hidden=[data['s2'].name, data['org2'].name, data['s3_inactive'].name],
            administrator=True,
        )

    def test_book_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse('admin:testapp_book_changelist'),
            visible=[data['b1'].name, data['org1'].name],
            hidden=[data['b2'].name, data['org2'].name, data['b3_inactive'].name],
            administrator=True,
        )

    def test_book_shelf_fk_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse('admin:testapp_book_add'),
            visible=[data['s1'].name],
            hidden=[data['s2'].name, data['s3_inactive'].name],
            select_widget=True,
            administrator=True,
        )
