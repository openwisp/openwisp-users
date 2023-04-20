class CreateMixin(object):
    def _create_book(self, **kwargs):
        options = dict(name='test-book', author='test-author')
        options.update(kwargs)
        b = self.book_model(**options)
        b.full_clean()
        b.save()
        return b

    def _create_shelf(self, **kwargs):
        options = dict(name='test-shelf')
        options.update(kwargs)
        s = self.shelf_model(**options)
        s.full_clean()
        s.save()
        return s

    def _create_template(self, **kwargs):
        options = dict(name='test-template')
        options.update(kwargs)
        t = self.template_model(**options)
        t.full_clean()
        t.save()
        return t

    def _create_library(self, **kwargs):
        options = dict(name='test-library', address='test-address')
        options.update(kwargs)
        lib = self.library_model(**options)
        lib.full_clean()
        lib.save()
        return lib

    def _create_tag(self, **kwargs):
        options = dict(name='test-tag')
        options.update(kwargs)
        tag = self.tag_model(**options)
        tag.full_clean()
        tag.save()
        return tag
