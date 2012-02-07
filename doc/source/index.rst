.. Django Swallow documentation master file, created by
   sphinx-quickstart on Wed Feb  1 15:56:59 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Django Swallow's documentation!
==========================================

Django Swallow is an utility Django application with which you can easly import
XML files and other documents even linked documents in database.

  « Simple things should be simple, complex things should be possible. » 
  `Alan Kay <http://en.wikipedia.org/wiki/Alan_Kay>`_

A simple import is defined as a set four classes ``Configuration``, 
a ``Builder`` linked to a triptych ``Mapper``, ``Populator`` and ``Model``. 
Each of which deals with specific problems. While it still makes a lot of 
classes to define, it strives for more *reusability* with 
`separatation of concerns <http://en.wikipedia.org/wiki/Separation_of_concerns>`_.

*Nested imports* or *Recursive imports* which deals with several documents 
linked to a main document will require for each document type a *triptych*. For 
instance, let's consider an html file linked to pictures and several feeds, such 
an import will be defined with a ``Configuration`` class and three *triptych*. 
There is no limit on nesting degree except Python runtime limits.

An import can be run by a **cron**, preferably `fcron <http://fcron.free.fr/>`_ 
using :mod:`swallow.management.commands.swallow` command.

Django Swallow has an **admin interface** integrated to Django admin that 
let you monitor progress and failed imports.

Django Swallow is `WTF <http://en.wikipedia.org/wiki/WTFPL>`_ licensed 
and hosted on `github <https://github.com/liberation/django-swallow>`_.

Getting started
---------------

Once it is shipped you will be able to::

   pip install django-swallow

Until then you can tinker with the example project found in the 
`forge <https://github.com/liberation/django-swallow/tree/master/example>`_
use the following command to retrieve the code::

  git clone https://github.com/liberation/django-swallow.git

Don't forget to have a look at the walkthrough.

Project configuration
---------------------

Define the following constants in you settings file, they may or may
not be needed, read carefully.

``SWALLOW_DIRECTORY``
~~~~~~~~~~~~~~~~~~~~~

**If** you use default ``Configuration`` swallow directories, you **must**
define this path. It will be used as the root directory for every configuration
that has not defined custom swallow directory. If you don't know, most likely
you will need to define this constant.

``SWALLOW_CONFIGURATION_MODULES``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's similar in purpose to Django's ``INSTALLED_APPS``, it must be a list
of monitored imports.

**If** you want to monitor an import in the admin, the module path
to the configuration class that defines the import should be in this list.

Contents
========

.. toctree::
   :maxdepth: 6

   walkthrough
   matching
   nested_builders
   advanced
   api/swallow

Glossary
========

.. glossary::

  Builder

    ``Builder`` classes handles the logic between a ``Mapper``, a ``Populator``
    and a Django ``Model``.

  Configuration

    A ``Configuration`` class is the root class defining your imports.

  Mapper

    ``Mapper`` retrieves values from a document.

  Populator

    ``Populator`` classes populates a ``Model`` instance.

  Swallow Directory

    A Swallow directory is a one of ``input``, ``work``, ``done``, ``error``
    used respectivly by Django Swallow, to look for new files to import, store
    files during import, store completed import files, store erronous files.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

