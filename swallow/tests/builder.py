from django.test import TestCase

from swallow.exception import StopImport

from swallow.builder import BaseBuilder
from swallow.builder import OK, STOPPED_IMPORT, ERROR

from swallow.populator import BasePopulator
from swallow.mappers import BaseMapper

from swallow.tests import RelatedM2M
from swallow.tests import ModelForBuilderTests


class BuilderNotImplementedErrorsTests(TestCase):
    """BaseBuilder has certains attributes that should be overriden check
    that these methods and properties raise a NotImplementedError exception"""

    def test_mapper(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(NotImplementedError, lambda : builder.Mapper)

    def test_model(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(NotImplementedError, lambda : builder.Model)

    def test_populator(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(NotImplementedError, lambda : builder.Populator)

    def test_instance_is_locally_modified(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(
            NotImplementedError,
            builder.instance_is_locally_modified,
            None
        )

    def test_skip(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(
            NotImplementedError,
            builder.skip,
            None
        )


class BuilderGetOrCreateTests(TestCase):

    class Builder(BaseBuilder):

        Model = ModelForBuilderTests

    class Mapper(BaseMapper):

        simple_field = 1

        @property
        def _instance_filters(self):
            return {'simple_field': 1}

    def test_get_or_create_instance_create(self):
        """Builder.get_or_create_instance if no instance
        exists it created one but without saving"""
        mapper = self.Mapper(None)
        builder = self.Builder(None, None)
        instance = builder.get_or_create_instance(mapper)
        # builder get_or_create does not save
        self.assertIsNone(instance.pk)
        self.assertEqual(1, instance.simple_field)

    def test_get_or_create_instance_create(self):
        """Builder.get_or_create_instance doesn't create an
        instance if it already exists"""
        ModelForBuilderTests(simple_field=1).save()

        mapper = self.Mapper(None)
        builder = self.Builder(None, None)
        instance = builder.get_or_create_instance(mapper)
        self.assertEqual(1, instance.simple_field)
        # the instance is fetched from db
        self.assertIsNotNone(instance.pk)
        self.assertEqual(1, ModelForBuilderTests.objects.all().count())
        db_instance = ModelForBuilderTests.objects.all()[0]
        self.assertEqual(db_instance, instance)


class BuilderSetFieldTests(TestCase):

    def test_field_is_a_one_to_one(self):

        class Populator(object):
            _fields_one_to_one = ('simple_field',)

        class Mapper(object):
            simple_field = 123

        builder = BaseBuilder(None, None)
        populator = Populator()
        instance = ModelForBuilderTests()
        mapper = Mapper()


        builder.set_field(
            populator,
            instance,
            mapper,
            'simple_field',
        )

        self.assertEqual(123, instance.simple_field)

    def test_field_is_populated_via_populator_method(self):

        class Populator(BasePopulator):
            _fields_one_to_one = []

            def simple_field(self):
                self._instance.simple_field = 123

        builder = BaseBuilder(None, None)
        instance = ModelForBuilderTests()
        populator = Populator(None, instance, None, builder)

        builder.set_field(
            populator,
            instance,
            None,
            'simple_field',
        )

        self.assertEqual(123, instance.simple_field)

    def test_field_should_not_be_populated(self):
        class Populator(BasePopulator):
            _fields_one_to_one = []


        builder = BaseBuilder(None, None)
        instance = ModelForBuilderTests()
        populator = Populator(None, instance, None, builder)

        builder.set_field(
            populator,
            instance,
            None,
            'simple_field',
        )

        self.assertIsNone(instance.simple_field)


class BuilderSetM2MFieldTests(TestCase):

    def test_populate_through_method(self):
        """If the populator has a method with the same name as
        the field is it called"""

        class Populator(BasePopulator):

            def m2m(self):
                related = RelatedM2M()
                related.save()
                self.related = related
                self._instance.m2m.add(related)

        builder = BaseBuilder(None, None)
        instance = ModelForBuilderTests(simple_field=1)
        instance.save()
        populator = Populator(None, instance, None, builder)

        builder.set_m2m_field(populator, instance, 'm2m')

        self.assertEqual(1, instance.m2m.count())
        db_related = instance.m2m.all()[0]
        self.assertEqual(db_related, populator.related)

    def test_do_not_populate(self):
        """If there is no populator method with the proper
        name, nothing happens"""
        builder = BaseBuilder(None, None)
        instance = ModelForBuilderTests(simple_field=1)
        instance.save()

        builder.set_m2m_field(None, instance, 'm2m')

        self.assertEqual(0, instance.m2m.count())

    def test_clear_m2m(self):
        """Tests that set_m2m_field clear the m2m before calling
        populator method"""
        builder = BaseBuilder(None, None)
        instance = ModelForBuilderTests(simple_field=1)
        instance.save()

        builder.set_m2m_field(None, instance, 'm2m')

        self.assertEqual(0, instance.m2m.count())


class BuilderProcessAndSaveTests(TestCase):

    def test_full_builder(self):
        """Check that a fully working builder works"""

        class ArticleBuilder(BaseBuilder):

            Model = ModelForBuilderTests

            class Mapper(BaseMapper):

                @classmethod
                def _iter_mappers(cls, builder):
                    for i in [1,2,3,4,5,6,7]:
                        yield cls(i)

                @property
                def _instance_filters(self):
                    return {'simple_field': self.simple_field}

                @property
                def simple_field(self):
                    return self._content

            class Populator(BasePopulator):

                _fields_one_to_one = ('simple_field',)
                _fields_if_instance_already_exists = []
                _fields_if_instance_modified_from_last_import = []

                def m2m(self):
                    for i in range(self._mapper.simple_field):
                        related = RelatedM2M()
                        related.save()
                        self._instance.m2m.add(related)

                def relatedm2m_set(self):
                    for i in range(self._mapper.simple_field):
                        m = ModelForBuilderTests(simple_field=i)
                        self._instance.relatedm2m_set.add(m)

            def skip(self, mapper):
                return False

            def instance_is_locally_modified(self, instance):
                return False

        builder = ArticleBuilder(None, None)
        instances, status = builder.process_and_save()

        self.assertEqual(status, OK)
        self.assertEqual(7, len(instances))

    def test_skip_builder(self):
        """Tests that it skip for every mapper but one"""

        class ArticleBuilder(BaseBuilder):

            Model = ModelForBuilderTests

            class Mapper(BaseMapper):

                @classmethod
                def _iter_mappers(cls, builder):
                    for i in [1,2,3,4,5,6,7]:
                        yield cls(i)

                @property
                def _instance_filters(self):
                    return {'simple_field': self.simple_field}

                @property
                def simple_field(self):
                    return self._content

            class Populator(BasePopulator):

                _fields_one_to_one = ('simple_field',)
                _fields_if_instance_already_exists = []
                _fields_if_instance_modified_from_last_import = []

                def m2m(self):
                    for i in range(self._mapper.simple_field):
                        related = RelatedM2M()
                        related.save()
                        self._instance.m2m.add(related)

                def relatedm2m_set(self):
                    for i in range(self._mapper.simple_field):
                        m = ModelForBuilderTests(simple_field=i)
                        self._instance.relatedm2m_set.add(m)

            def skip(self, mapper):
                if mapper.simple_field == 1:
                    return False
                else:
                    return True

            def instance_is_locally_modified(self, instance):
                return False

        builder = ArticleBuilder(None, None)
        instances, status = builder.process_and_save()

        self.assertEqual(status, OK)
        self.assertEqual(1, len(instances))
        self.assertEqual(1, instances[0].simple_field)

    def test_stop_import_on_simple_field(self):

        class ArticleBuilder(BaseBuilder):

            Model = ModelForBuilderTests

            class Mapper(BaseMapper):

                @classmethod
                def _iter_mappers(cls, builder):
                    for i in [1,2,3,4,5,6,7]:
                        yield cls(i)

                @property
                def _instance_filters(self):
                    return {'simple_field': self.simple_field}

                @property
                def simple_field(self):
                    return self._content

                @property
                def second_field(self):
                    if self.simple_field == 1:
                        return 42
                    raise StopImport()

            class Populator(BasePopulator):

                _fields_one_to_one = ('simple_field', 'second_field')
                _fields_if_instance_already_exists = []
                _fields_if_instance_modified_from_last_import = []

                def m2m(self):
                    for i in range(self._mapper.simple_field):
                        related = RelatedM2M()
                        related.save()
                        self._instance.m2m.add(related)

                def relatedm2m_set(self):
                    for i in range(self._mapper.simple_field):
                        m = ModelForBuilderTests(simple_field=i)
                        self._instance.relatedm2m_set.add(m)

            def skip(self, mapper):
                return False

            def instance_is_locally_modified(self, instance):
                return False

        builder = ArticleBuilder(None, None)
        instances, status = builder.process_and_save()

        self.assertEqual(status, STOPPED_IMPORT)
        self.assertEqual(1, len(instances))
        self.assertEqual(1, ModelForBuilderTests.objects.count())
        self.assertEqual(1, RelatedM2M.objects.count())

    def test_stop_import_on_m2m_field(self):

        class ArticleBuilder(BaseBuilder):

            Model = ModelForBuilderTests

            class Mapper(BaseMapper):

                @classmethod
                def _iter_mappers(cls, builder):
                    for i in [1,2,3,4,5,6,7]:
                        yield cls(i)

                @property
                def _instance_filters(self):
                    return {'simple_field': self.simple_field}

                @property
                def simple_field(self):
                    return self._content

                @property
                def second_field(self):
                    return 2

            class Populator(BasePopulator):

                _fields_one_to_one = ('simple_field', 'second_field')
                _fields_if_instance_already_exists = []
                _fields_if_instance_modified_from_last_import = []

                def m2m(self):
                    if self._mapper.simple_field != 1:
                        raise StopImport()
                    for i in range(self._mapper.simple_field):
                        related = RelatedM2M()
                        related.save()
                        self._instance.m2m.add(related)

                def relatedm2m_set(self):
                    for i in range(self._mapper.simple_field):
                        m = ModelForBuilderTests(simple_field=i)
                        self._instance.relatedm2m_set.add(m)

            def skip(self, mapper):
                return False

            def instance_is_locally_modified(self, instance):
                return False

        builder = ArticleBuilder(None, None)
        instances, status = builder.process_and_save()

        self.assertEqual(status, STOPPED_IMPORT)
        self.assertEqual(1, len(instances))
        self.assertEqual(1, ModelForBuilderTests.objects.count())
        self.assertEqual(1, RelatedM2M.objects.count())


    def test_stop_import_on_related_m2m_field(self):
        pass

    def test_error_on_simple_field(self):
        pass

    def test_error_on_m2m_field(self):
        pass

    def test_error_on_related_m2m_field(self):
        pass

    def test_integrity_error_on_save(self):
        pass

    def test_call_set_field_on_simple_field(self):
        pass

    def test_call_set_m2m_field_on_m2m_field(self):
        pass

    def test_call_set_m2m_field_on_related_m2m_field(self):
        pass
