from openwisp_users.api.mixins import (
    FilterSerializerByOrgManaged,
    FilterSerializerByOrgMembership,
    FilterSerializerByOrgOwned,
)
from openwisp_utils.api.serializers import ValidatedModelSerializer

from .models import Book, Library, Shelf, Template


class BookMemberSerializer(FilterSerializerByOrgMembership, ValidatedModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class BookManagerSerializer(FilterSerializerByOrgManaged, ValidatedModelSerializer):
    include_shared = True

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


class LibrarySerializer(FilterSerializerByOrgManaged, ValidatedModelSerializer):
    class Meta:
        model = Library
        fields = '__all__'


class ShelfSerializerForBook(FilterSerializerByOrgManaged, ValidatedModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'
        read_only_fields = ('created', 'modified')


class BookWithNestedShelfSerializer(
    FilterSerializerByOrgManaged, ValidatedModelSerializer
):
    shelf = ShelfSerializerForBook()

    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created', 'modified')

    def validate(self, data):
        if data.get('shelf'):
            shelf_data = data.pop('shelf')
            shelf_obj = Shelf.objects.create(**shelf_data)
        data.update({'shelf': shelf_obj})
        instance = self.instance or self.Meta.model(**data)
        instance.full_clean()
        return data


class ShelfWithReadOnlyOrgSerializer(
    FilterSerializerByOrgManaged, ValidatedModelSerializer
):
    class Meta:
        model = Shelf
        fields = '__all__'
        read_only_fields = ('organization', 'created', 'modified')
