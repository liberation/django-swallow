Walkthrough
===========

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

You might like to group configuration and related triptychs in a module, you 
most likely will circuvent this convention if you need to do factorisation.

If you have several imports you might want to store all configuration in one 
Django application.  A possible solution to deal with this situation 
is to use a django application to store all the imports within a module named 
after its import feature. If we used this convention in the example 
project ``config.py``, would be named ``github``, ``feed`` or 
``feed_import`` to better emphasizes what the module purpose is.

Creating a django application is not required but handy if you want to run
all your tests with django test runner.


Configuration
-------------

A *Configuration* class defines an import feature, you will most likely name 
it after the job the import get done.

This class specialize on several aspects of the import:

- It defines an import, imports are run via this class.
- Finds input files to import, move them between the different swallow directory
- It selectively loads a Builder class for files.

Example of simple configuration class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  .. code-block:: python

    class Github(BaseConfig):

        def load_builder(self, path, f):
            return FeedBuilder(path, f, self)

With this kind of configuration you *must* define ``SWALLOW_DIRECTORY`` in your 
settings. Inside this directory Swallow will create a folder named after 
the configuration class, in this case ``github``, and store in ``work``, 
``error``, ``done`` the imported files. 
**You have to create the ``input`` directory by yourself**

The purpose of ``load_builder`` is to load a *builder* class for a given file 
to do the actual import. If ``load_builder`` returns ``None`` swallow won't
process the file and leave it in *input* directory. Example application's 
configuration class takes advantage of this feature, so that the import only
consider file with an "atom" extension:

  .. code-block:: python

    class Github(BaseConfig):

        def load_builder(self, path, f):
            if path.endswith('.atom'):
                return FeedBuilder(path, f, self)

This feature allow you to use the same input directory for several imports.

This configuration only returns one type of builder, we can also imagine that
the builder returns a builder depending of the extension of ``path``.

Builder
-------

The *builder* class connects together the other component of the import
and a django model. It deals with aspects of the import that or not related
to other parts of 
