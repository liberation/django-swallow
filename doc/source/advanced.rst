Advanced usage
==============


How to keep swallow classes organized ?
---------------------------------------

You might like to group configuration, builder and related triptychs in a 
module like it is done in the example application. You most likely will 
circuvent this convention if you need to do factorisation.

If you have several imports you might want to store all import modules in one 
Django application. A possible solution to deal with this situation 
is to use a django application to store all the imports within a module named 
after its import feature. If we used this convention in the example 
project ``config.py``, would be named ``github``, ``feed`` or 
``feed_import`` to better emphasizes what the module purpose is.

Creating a django application is not required but handy if you want to run
all your tests with django test runner.


How to handle subdocuments ?
----------------------------


All subdocuments are the same
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If all subdocuments have the same format, like RSS and ATOM files, you can 
implement a ``Mapper._iter_mappers`` class method which yield one mapper 
per subdocument. If you need to link resulting model instance objects together 
you can:

1. Implement a ``postprocess`` method in configuration that takes as argument 
   the list of resulting objects.
2. Override ``swallow.BaseBuilder.process_and_save`` and do something useful
   before returning the instances. This solution is the only way to postprocess
   instances built by a nested builder.

Subdocuments are different
^^^^^^^^^^^^^^^^^^^^^^^^^^

To find a solution to this problem, you need to know how subdocuments are
linked together ?

Possible solutions are:

- Nested builders make it possible to populate an instance field 
  with the value(s) returned by a builder.

- Inspect the document and load several builders in ``Configuration.load_builder`` 
  You can link objects together in the postprocessing step.

- If a document contains an heterogeneous set of subdocuments where the link 
  information is in the document and you cannot use nested builder, you will 
  need to use a special builder to retrieve associations information and 
  returns it as if it was a model instance object. Then in the postprocessing 
  step you can do something like:

  .. code-block:: python

    # postprocess method of a configuration

    def postprocess(self, instances):
        # head is associations information
        # it's the first builders returned by ``load_builders``
        associations, instances = instances[0], instances[1:]
        for start_identifier, end_identifier in associations:
            # an association is tuple (identifier_start, identifier_end)
            start = find_instance(instances, start_identifier)
            end = find_instance(instances, end_identifier)
            connect(start, end)


Populator patterns
------------------

If the builder find a field in the model instance it first check
for a one to one population. If the field name is not found in 
``_fields_one_to_one`` property of the populator, the builder try
to call a method with the same name as the field. If it exists it's
up to the method to do proper population with distintive code for
complex value computation, foreign key, simple M2M fields and M2M fields
supported by a through model. The population method has no parameters,
instead the populator reference mapper and model instance respectivly as 
``self._mapper`` and ``self._instance``. You don't necessarily need 
to populate only the field for which the method was called, that said
it's not recommanded.
