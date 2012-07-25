Nested Builders
===============

Sometimes documents are nested inside other documents. For instance, in the ATOM
file format entry elements are defined inside feed elements. Both of them can be
defined as separate Django models.

Imagine an import feature that takes as input any ATOM file has to 
create / update the blog information from which the feed is downloaded 
and create / update any entry it finds in the feed and attach them to 
the blog. Such an import should use nested builders.

This import use two builders ``FeedBuilder`` and ``EntryBuilder``. 
``FeedBuilder`` will use ``EntryBuilder`` to build entries and then retrieve
each entries object to attach them to the blog.

First let's mock the code that is related to the ``FeedMapper``.

``FeedMapper`` should have a ``entries`` property that generates a list of 
entry nodes. 

  .. code-block:: python

    from swallow.mappers import BaseMapper


    class FeedMapper(BaseMapper):

        # ...

       @property
       def entries(entries):
           for entry in self._item.xpath('.//entry'):
               yield entry

Related ``FeedPopulator`` ``entries`` method looks like:

  .. code-block:: python

    from swallow.builder import from_builder
    from swallow.populator import BasePopulator


    class FeedPopulator(BasePopulator):

        # ...

        @from_builder(EntryBuilder)
        def entries(self, entries):
            self._instance.entries.clear()
            for entry in entries
                self._instance.entries.add(entry)

It's done. Really. The reamining code is built just like a plain import. The 
only difference is that ``EntryMapper`` ``_iter_mappers`` has its parameter
``f`` bound to a node in an xml file.

  .. code-block:: python

    # in EntryMapper class body

    @classmethod
    def _iter_mappers(cls, path, f):
        # f is lxml node
        yield cls(f, path)
