Matching
========

Matching is facility provided by Django Swallow that allows to build 
population algorithm that are a bit more advanced than one to one population 
already available through a populator class. It also allows any user having
access to the admin area to tweak the algorithm.

Matching Model
--------------

Django Swallow defines a django model named Matching composed of a ``name`` 
and a ``file`` which holds the xml defining the algorithm used to do the match.

The matching file allows you to define matching rules.

An example matching xml file follows:

.. code-block:: xml

  <maps default="ninja">
    <map>
      <column>OUTPUT</column>
        <set>
          <title>foo</title>
          <title>bar</title>
          <suptitle>baz</suptitle>
        </set>
      <set>
        <suptitle loose-compare="yes">éèçàæœ et voilà</suptitle>
      </set>
    </map>
  </maps>

It defines a list of  ``map`` elements. Each map defines a value
to be outputed as ``column`` element. If one ``set`` element is
a match, the ``column`` value should be returned. Each set defines
rules. Each elements of a set should have the name of a mapper
property. Each of them is a rule, they are ANDed to form the set-rule.
If several element inside a set have the same name, they are ORed together
before being ANDed as rules of the set.
For instance the first set in the example matching file generate a code
equivalent to:

.. code-block:: python

  (mapper.title == "foo" or mapper.title == "bar") and mapper.suptitle == "baz"

If no map matchs and if a value is defined as default attribute in root elements, 
it is returned.


``from_matching``
-----------------

``Matching`` model class has a method decorator class attribute named 
``from_matching`` that can be used to decorate populator class methods. It 
allows you to inject the result(s) of the match as an argument of the 
population method.
