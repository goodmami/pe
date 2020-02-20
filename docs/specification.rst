
Parsing Expressions Specification
=================================

This document defines the expressions available to **pe**.

Terms
-----

.. code::

   .        # Dot: any single character
   "abc"    # Literal: a character sequence
   'abc'    # Literal
   [abc]    # Character class: a single character from the set
   [^abc]   # Negated character class: a single character not in the set


Dot
'''

``.``


Literal
'''''''

``"abc"``


Character Class
'''''''''''''''

``[abc]``

``[^abc]``


Expressions
-----------

.. code::

   e1 e2    # Sequence
   e1 | e2  # Choice
   e?       # Optional; 0 or 1 occurrences
   e*       # Repeat of 0 or more occurrences
   e+       # Repeat of 1 or more occurrences
   e{i}     # Repeat of exactly i occurrences
   e{i,j}   # Repeat of i to j occurrences
   e{i:d}   # Repeat of exactly i occurences delimited by d
   e{i,j:d} # Repeat of i to j occurrences delimited by d
   (e)      # Capturing group
   (?:e)    # Non-capturing group
   Name     # Non-terminal named 'Name'
   Name = e # Grammar rule mapping 'Name' to an expression


Repeat
''''''

Repetition in **pe** expands the notion from regular expressions to
allow for two new features:

- Delimiter expressions -- repeat if expression succeeds
- Escape expressions -- accept before or after repetitions

Thus, including the minimum and maximum, the :class:`~pe.Repeat`
expression has five fields.

==============  =====================================
Shorthand       Equivalent
==============  =====================================
``e{1}``        ``e``
``e{2}``        ``e e`` (etc.)
``e?``          ``e{,1}``
``e*``          ``e{,}``
``e+``          ``e{1,}``
``e{1,:d}``     ``e (?: d e )*``
``e{:,x}``      ``(?: x* e x*)*`` or ``(?: x | e )*``
``e{1,3:d,x}``  ``x* e x* (?: d x* e x* ){,2}``
==============  =====================================

..
  .           # any single character
  "abc"       # literal
  'abc'       # literal
  [abc]       # character class
  [^abc]      # negated character class

  # repeating expressions
  e           # exactly one
  e?          # zero or one (optional)
  e*          # zero or more
  e+          # one or more
  e{2:d}      # exactly two delimited by d (delimiter optional)
  e{2,5:d}    # between two and five delimited by d (all parameters optional)

  # combining expressions
  e1 e2       # sequence of e1 and e2
  e1 | e2     # ordered choice of e1 and e2
  (?:e)       # non-capturing group
  (e)         # capturing group

  # lookahead
  &e          # positive lookahead
  !e          # negative lookahead

  # grammars
  name = ...  # define a rule named 'name'
  ... = name  # refer to rule named 'name'
