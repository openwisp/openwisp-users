from openwisp_utils.api.serializers import ValidatedModelSerializer

from openwisp_users.api.mixins import (
    FilterSerializerByOrgManaged,
    FilterSerializerByOrgMembership,
    FilterSerializerByOrgOwned,
)

from .models import Book, Shelf, Template


class BookMemberSerializer(FilterSerializerByOrgMembership, ValidatedModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class BookManagerSerializer(FilterSerializerByOrgManaged, ValidatedModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class BookOwnerSerializer(FilterSerializerByOrgOwned, ValidatedModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class BookSerializer(ValidatedModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class ShelfSerializer(ValidatedModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class TemplateSerializer(FilterSerializerByOrgManaged, ValidatedModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'
