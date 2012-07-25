Walkthrough Tutorial
====================

We will study the example application. It can be found in the 
`forge <https://github.com/liberation/django-swallow/tree/master/example>`_
use the following command to retrieve the code::

  git clone https://github.com/liberation/django-swallow.git

Then open in your favorite editor the interesting files::

  emacs django-swallow/example/config.py django-swallow/example/settings.py


``config.py``
-------------

``example/config.py`` contains all the classes for importing feeds, it has 
a LOC feature of 59.


Configuration
-------------

A configuration class defines an import feature, you will most likely name 
it after the job the import get done.

This class specialize on several aspects of the import:

- It defines an import, imports are run via this class.
- Finds input files to import, move them between the different swallow directory
- It selectively loads a Builder class for files.

For instance, you can implement a configuration class like this one:

  .. code-block:: python

    class Github(BaseConfig):

        def load_builder(self, path, f):
            return FeedBuilder(path, f, self)

With this kind of configuration you *must* define ``SWALLOW_DIRECTORY`` in your 
settings. Inside this directory Swallow will create a folder named after 
the configuration class, in this case ``github``, and store in it ``work``, 
``error``, ``done`` the imported files. 

.. note::

  You have to create the ``input`` directory yourself

The purpose of ``load_builder`` is to instanciate a *builder* class for a given 
file to do the actual import. If ``load_builder`` returns ``None`` swallow won't
process the file and leave it in *input* directory. Example's configuration 
class takes advantage of this feature, so that the import only consider file 
with an "atom" extension:

  .. code-block:: python

    class Github(BaseConfig):

        def load_builder(self, path, f):
            if path.endswith('.atom'):
                return FeedBuilder(path, f, self)

This feature allow you to use the same input directory for several imports.

This configuration only returns one type of builder, we can also imagine that
the builder returns a builder depending of the extension of ``path``.

Triptych classes
----------------

Before explaining what a builder class, we will concentrate on its dependencies,
Model, Mapper and Populator classes.

Model
~~~~~

Model class is Django Model class it's most likely defined in an application 
``models.py`` file. Django swallow was built to be unobtrusive but you might 
need to add some fields to your models to support update and update with 
modification.

Mapper
~~~~~~

A Mapper class has the responsability to:

- build mapper instance objects for a given document
- provide a dictionary with which the builder will instantiate a model
- provide a certain number of properties to access document values

Let's imagine a set of documents where the first line is the title and the 
second line the body. A mapper for this kind of file can be:

  .. code-block:: python

    from swallow.mapper import BaseMapper


    class LineBasedDocumentMapper(DefaultMapper):

        def __init__(self, item, path, title, body):
            super(LineBasedDocumentMapper, self).__init__(item, path)
            self.title = title
            self.body = body

        @classmethod
        def _iter_mappers(cls, file_path, f):
            title = f.readline()
            body = f.readline()
            yield cls(f, file_path, title, body)

        def _instance_filter(self):
            return {'title': self.title}


``_iter_mappers`` is a generator method that yields mapper instances. It 
must only yield mapper instances of the class it is defined in.

In the example, the mapper is defined inside the builder class, let's study it:

  .. code-block:: python

    from mappers import BaseMapper


    NS = {'n':'http://www.w3.org/2005/Atom'}


    class Mapper(BaseMapper):

        def __init__(self, item):
            self.item = item

        @classmethod
        def _iter_mappers(cls, file_path, f):
            xml = etree.parse(f)
            root = xml.getroot()
            for item in root.xpath('.//n:entry', namespaces=NS):
                yield cls(item)

        @property
        def _instance_filters(self):
            return {'title': self.title}

        @property
        def title(self):
            return self.item.xpath('.//n:title', namespaces=NS)[0].text[:255]

        @property
        def content(self):
            return self.item.xpath('.//n:content', namespaces=NS)[0].text

It similar in purpose to the first mapper but instead of line based document,
the factory method ``_iter_mappers`` takes as ``f`` argument variable a handle
to an xml file. One document can contains several subdocuments, each subdocument
is mapped by a mapper. It's a common pattern when you deal with documents 
embedded in a main document like ATOM or RSS file format.


Populator
~~~~~~~~~

Populator handles instance model object population. It configures how the
import should be done in different cases. The simplest populator is:

  .. code-block:: python

   class Populator(BasePopulator):

        _fields_one_to_one = ('some', 'properties', 'found', 'in', 'mapper')
        _fields_if_instance_already_exists = []
        _fields_if_instance_modified_from_last_import = []

What it does is fetch values of 'some', 'attributes', 'found', 'in', 'mapper' 
mapper's properties and set instance model fields with the proper value. Model 
instance fields are matched one to one with their name as mapper properties, 
which means that ``an_instance.some`` will have its values set to 
``a_mapper.some``.
If the instance exists prior to import, no field will be set. If the 
instance existed prior to current import and instance was modified, no field
will be set too.


.. note::

  Builder class has a way to know if an instance model was created or not, 
  and if it wasn't created whether it was modified by the application or not.

The populator found in the example is similar:

  .. code-block:: python

    from populator import BasePopulator
    
    
    class Populator(BasePopulator):
    
        _fields_one_to_one = ('title', 'content')
        _fields_if_instance_already_exists = None
        _fields_if_instance_modified_from_last_import = None

``None`` value means in this case that all fields will be be set by
the builder.

More complex population patterns exists see Advanced usage, Matching and 
Nested Builders chapters.


Builder
-------

The builder class connects together a mapper, populator and 
model. It requests values from the mapper and populates model 
instances with the help of the Populator.

A builder class in its short form can look like:

  .. code-block:: python

    class SimpleBuilder(BaseBuilder):

        Model = DjangoModel
        Mapper = DocumentMapper
        Populator = DjangoModelPopulator

        def skip(self, mapper):
            return False

        def instance_is_locally_modified(self, instance):
            return False

``Mapper`` and ``Populator`` classes can be inlined in the class definition, 
it is the case of the Mapper class in the following snippet:

  .. code-block:: python

    class SimpleBuilder(BaseBuilder):

        Model = DjangoModel

        class Mapper:

            @classmethod
            def _iter_mapper(cls, path, f):
                yield cls(f, path)

      Populator = DjangoModelPopulator

      def skip(self, mapper):
          return False

      def instance_is_locally_modified(self, instance):
          return False

A builder should implement two methods ``skip`` and 
``instance_is_locally_modified``. The former tells the builder whether or not
to skip the import of a specific mapper. The latter is used to know wether
the instance object was modified. This can be implemented in several ways
depending on you model class. A solution is to use an author field, ``SWALLOW`` 
will be used as a value when the import create the instance for the first
time and the field changes value when an user edit the object.

  .. code-block:: python

      def instance_is_locally_modified(self, instance):
          return instance.author != 'SWALLOW'
