import swapper
from django_filters import rest_framework as filters
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from openwisp_users.api.authentication import BearerAuthentication
from openwisp_users.api.filters import (
    OrganizationManagedFilter,
    OrganizationMembershipFilter,
    OrganizationOwnedFilter,
)
from openwisp_users.api.mixins import (
    FilterByOrganizationManaged,
    FilterByOrganizationMembership,
    FilterByOrganizationOwned,
    FilterByParentManaged,
    FilterByParentMembership,
    FilterByParentOwned,
    FilterDjangoByOrgManaged,
)
from openwisp_users.api.permissions import (
    BaseOrganizationPermission,
    DjangoModelPermissions,
    IsOrganizationManager,
    IsOrganizationMember,
    IsOrganizationOwner,
)

from .models import Book, Config, Library, Shelf, Template
from .serializers import (
    BookManagerSerializer,
    BookMemberSerializer,
    BookOwnerSerializer,
    BookSerializer,
    BookWithNestedShelfSerializer,
    LibrarySerializer,
    ShelfSerializer,
    ShelfWithReadOnlyOrgSerializer,
    TemplateSerializer,
)

Organization = swapper.load_model('openwisp_users', 'Organization')


class BookOrgMixin:
    def get_parent_queryset(self):
        shelf_org = Shelf.objects.get(pk=self.kwargs['shelf_id']).organization
        qs = Book.objects.filter(organization=shelf_org.pk)
        return qs


class BaseGetApiView(APIView):
    queryset = Template.objects.all()

    def get(self, request, *args, **kwargs):
        testorg, _ = Organization.objects.get_or_create(name='test org')
        template, _ = Template.objects.get_or_create(
            name='sample', organization=testorg
        )
        self.check_object_permissions(request, template)
        return Response({})


class ApiMemberView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)


class ApiManagerView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationManager,)


class ApiOwnerView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationOwner,)


class BaseOrganizationPermissionView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (BaseOrganizationPermission,)


class OrganizationFieldView(APIView):
    queryset = Config.objects.all()
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    organization_field = 'template__organization'

    def get(self, request, *args, **kwargs):
        testorg, _ = Organization.objects.get_or_create(name='test org')
        temp1, _ = Template.objects.get_or_create(name='temp', organization=testorg)
        config, _ = Config.objects.get_or_create(template=temp1, organization=testorg)
        self.check_object_permissions(request, config)
        return Response({})


class ErrorOrganizationFieldView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    organization_field = 'error__organization'


class ShelfListMemberFilter(OrganizationMembershipFilter):
    class Meta(OrganizationMembershipFilter.Meta):
        model = Shelf
        fields = OrganizationMembershipFilter.Meta.fields + ['tags']


class ShelfListMemberView(FilterByOrganizationMembership, ListAPIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    serializer_class = ShelfSerializer
    queryset = Shelf.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ShelfListMemberFilter


class ShelfListManagerFilter(OrganizationManagedFilter):
    class Meta(OrganizationManagedFilter.Meta):
        model = Shelf
        fields = OrganizationManagedFilter.Meta.fields + ['tags']


class ShelfListManagerView(FilterByOrganizationManaged, ListAPIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationManager,)
    serializer_class = ShelfSerializer
    queryset = Shelf.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ShelfListManagerFilter


class ShelfListOwnerFilter(OrganizationOwnedFilter):
    class Meta(OrganizationOwnedFilter.Meta):
        model = Shelf
        fields = OrganizationOwnedFilter.Meta.fields + ['tags']


class ShelfListOwnerView(FilterByOrganizationOwned, ListAPIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationOwner,)
    serializer_class = ShelfSerializer
    queryset = Shelf.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ShelfListOwnerFilter


class BooksListMemberView(BookOrgMixin, FilterByParentMembership, ListCreateAPIView):
    queryset = Book.objects.none()
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    serializer_class = BookMemberSerializer

    def get_queryset(self):
        shelf = Shelf.objects.get(pk=self.kwargs['shelf_id'])
        super().get_queryset()
        return shelf.book_set.all()


class BooksListManagerView(BookOrgMixin, FilterByParentManaged, ListCreateAPIView):
    queryset = Book.objects.none()
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationManager,)
    serializer_class = BookManagerSerializer

    def get_queryset(self):
        shelf = Shelf.objects.get(pk=self.kwargs['shelf_id'])
        super().get_queryset()
        return shelf.book_set.all()


class BooksListOwnerView(BookOrgMixin, FilterByParentOwned, ListCreateAPIView):
    queryset = Book.objects.none()
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationOwner,)
    serializer_class = BookOwnerSerializer

    def get_queryset(self):
        shelf = Shelf.objects.get(pk=self.kwargs['shelf_id'])
        super().get_queryset()
        return shelf.book_set.all()


# some views may not contain `permission_classes` and have to be tested separately
class ShelfListUnauthorizedView(FilterByOrganizationMembership, ListAPIView):
    authentication_classes = (BearerAuthentication,)
    serializer_class = ShelfSerializer
    queryset = Shelf.objects.all()


class BooksListUnauthorizedView(BookOrgMixin, FilterByParentOwned, ListAPIView):
    queryset = Book.objects.none()
    authentication_classes = (BearerAuthentication,)
    serializer_class = BookSerializer

    def get_queryset(self):
        shelf = Shelf.objects.get(pk=self.kwargs['shelf_id'])
        super().get_queryset()
        return shelf.book_set.all()


class TemplateListCreateView(FilterByOrganizationManaged, ListCreateAPIView):
    serializer_class = TemplateSerializer
    authentication_classes = (BearerAuthentication,)
    permission_classes = (
        IsOrganizationMember,
        DjangoModelPermissions,
    )
    queryset = Template.objects.all()


class TemplateDetailView(FilterByOrganizationManaged, RetrieveUpdateDestroyAPIView):
    serializer_class = TemplateSerializer
    authentication_classes = (BearerAuthentication,)
    permission_classes = (
        IsOrganizationMember,
        DjangoModelPermissions,
    )
    queryset = Template.objects.all()


class LibraryListFilter(FilterDjangoByOrgManaged):
    class Meta:
        model = Library
        fields = (
            'book',
            'book__organization',
        )


class LibraryListCreateView(FilterByOrganizationManaged, ListCreateAPIView):
    serializer_class = LibrarySerializer
    organization_field = 'book__organization'
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    queryset = Library.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = LibraryListFilter


class LibraryDetailView(FilterByOrganizationManaged, RetrieveUpdateDestroyAPIView):
    serializer_class = LibrarySerializer
    organization_field = 'book__organization'
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    queryset = Library.objects.all()


class BookNestedShelfListCreateView(FilterByOrganizationManaged, ListCreateAPIView):
    serializer_class = BookWithNestedShelfSerializer
    authentication_classes = (BearerAuthentication,)
    permission_classes = (
        IsOrganizationMember,
        DjangoModelPermissions,
    )
    queryset = Book.objects.all()


class ShelfWithReadOnlyOrgListCreateView(
    FilterByOrganizationManaged, ListCreateAPIView
):
    serializer_class = ShelfWithReadOnlyOrgSerializer
    queryset = Shelf.objects.all()


api_member_view = ApiMemberView.as_view()
api_manager_view = ApiManagerView.as_view()
api_owner_view = ApiOwnerView.as_view()
base_org_view = BaseOrganizationPermissionView.as_view()
org_field_view = OrganizationFieldView.as_view()
error_field_view = ErrorOrganizationFieldView.as_view()
books_list_member_view = BooksListMemberView.as_view()
books_list_manager_view = BooksListManagerView.as_view()
books_list_owner_view = BooksListOwnerView.as_view()
book_list_unauthorized_view = BooksListUnauthorizedView.as_view()
shelf_list_unauthorized_view = ShelfListUnauthorizedView.as_view()
shelf_list_member_view = ShelfListMemberView.as_view()
shelf_list_manager_view = ShelfListManagerView.as_view()
shelf_list_owner_view = ShelfListOwnerView.as_view()
template_list = TemplateListCreateView.as_view()
template_detail = TemplateDetailView.as_view()
library_list = LibraryListCreateView.as_view()
library_detail = LibraryDetailView.as_view()
book_nested_shelf = BookNestedShelfListCreateView.as_view()
shelf_with_read_only_org_view = ShelfWithReadOnlyOrgListCreateView.as_view()
