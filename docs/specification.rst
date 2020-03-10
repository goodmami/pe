
=============
Specification
=============


Quick Reference
===============

.. code:: ruby

   # The following abbreviations are used below:
   #   Expression Types (E):            Value Types (V)
   #     e - a parsing expression         u - a unary value type
   #     p - a primary term               i - an iterable value type
   #     q - a quantified term            n - a nullary value type
   #     v - an evaluated term            d - a deferred value type
   #     s - a sequence                 Value/Binding Resolution:
   #   Other:                             $x - the value of x
   #     A - a nonterminal identifier     %x - the bindings of x
   #     name - a binding identifier      ~x - (as a value) the substring matched by x

   # Op        Name      Value-Type  Description

   ### Primary Terms (p)
     .       # Dot       Unary       any single character
     "abc"   # Literal   Unary       the string 'abc'
     'abc'   # Literal   Unary       the string 'abc'
     [abc]   # Class     Unary       any one character in 'abc'
     A       # Symbol    Deferred    rule A
     (e)     # Group     Deferred    parsing expression e

   ### Quantified Terms (q)
     p       #           Deferred
     p?      # Optional  Iterable    p zero or one times
     p*      # Star      Iterable    p zero or more times
     p+      # Plus      Iterable    p one or more times

   ### Evaluated Terms (v)
     q       #           Deferred    quantified term q
     &q      # And       Nullary     q, but consume no input
     !q      # Not       Nullary     not q, but consume no input
     name:q  # Bind      Nullary     q
     :q      # Bind      Nullary     q
     ~q      # Raw       Unary       q
     q

   ### Sequences (s)
     v       #           Deferred    evaluated term v
     v s     # Sequence  Iterable    v then sequence s

   ### Choices (e)
     s       #           Deferred    sequence s
     s / e   # Choice    Iterable    e only if s failed

   ### Grammars (r)
     A <- e  # Rule      Deferred    parsing expression e
     A <~ e  # Rule      Deferred    short for A <- ~(e)


Grammar Syntax
==============

The following is a formal description of **pe**'s PEG syntax describing
itself. This PEG is based on Bryan Ford's original `paper
<https://bford.info/pub/lang/peg>`_.

.. code:: ruby

  # Hierarchical syntax
  Start      <- :Spacing (Expression / Grammar) :EndOfFile
  Grammar    <- Definition+
  Definition <- Identifier Operator Expression
  Operator   <- LEFTARROW / RAWARROW
  Expression <- Sequence (SLASH Sequence)*
  Sequence   <- Evaluated*
  Evaluated  <- Prefix? Quantified
  Prefix     <- AND / NOT / TILDE / Binding
  Binding    <- Name? :COLON
  Quantified <- Primary Quantifier?
  Quantifier <- QUESTION / STAR / PLUS
  Primary    <- Name / Group / Literal / Class / DOT
  Name       <- Identifier !Operator
  Group      <- :OPEN Expression :CLOSE

  # Lexical syntax
  Identifier <- ~(IdentStart IdentCont*) :Spacing
  IdentStart <- [a-zA-Z_]
  IdentCont  <- IdentStart / [0-9]

  Literal    <- :['] ~( !['] Char )* :['] :Spacing
              / :["] ~( !["] Char )* :["] :Spacing

  Class      <- :'[' ~( !']' Range )* :']' :Spacing
  Range      <- Char '-' Char / Char
  Char       <- '\\' . / .

  LEFTARROW  <- '<-' :Spacing
  RAWARROW   <- '<~' :Spacing
  SLASH      <- '/' :Spacing
  AND        <- '&' :Spacing
  NOT        <- '!' :Spacing
  TILDE      <- '~' :Spacing
  QUESTION   <- '?' :Spacing
  STAR       <- '*' :Spacing
  PLUS       <- '+' :Spacing
  OPEN       <- '(' :Spacing
  CLOSE      <- ')' :Spacing
  DOT        <- '.' :Spacing
  COLON      <- ':' :Spacing

  Spacing    <- (Space / Comment)*
  Comment    <- '#' (!EndOfLine .)* EndOfLine
  Space      <- ' ' / '\t' / EndOfLine
  EndOfLine  <- '\r\n' / '\n' / '\r'
  EndOfFile  <- !.


Operator Precedence
===================

===========  ========  ==========  ===============
Operator     Name      Precedence  Expression Type
===========  ========  ==========  ===============
``.``        Dot       5           Primary
``" "``      Literal   5           Primary
``[ ]``      Class     5           Primary
``Abc``      Name      5           Primary
``(e)``      Group     5           Primary
``e?``       Optional  4           Quantified
``e*``       Star      4           Quantified
``e+``       Plus      4           Quantified
``&e``       And       3           Evaluated
``!e``       Not       3           Evaluated
``:e``       Bind      3           Evaluated
``~e``       Raw       3           Evaluated
``e1 e2``    Sequence  2           Sequence
``e1 / e2``  Choice    1           Expression
===========  ========  ==========  ===============


Semantic Values
===============

The value of each expression is a list. For 


Expressions
===========

This document defines the expressions available to **pe**.

Dot
---

:form:            ``.``
:expression-type: primary
:value-type:      atomic



The Dot operator always succeeds if there is any remaining input and
fails otherwise. It consumes a single character.



Literal
-------

``"abc"``


Character Class
---------------

``[abc]``


Nonterminal Symbol
------------------

``A``


Group
-----

``(e)``

Groups do not actually refer to a construct in **pe**, but they are
used to aid in the parsing of a grammar. This is helpful when one
wants to apply a lower-precedence operator with a higher-precedence
one, such as a sequence of choices::

  [0-9] ' and ' / ' or ' [0-9]    # parses "1 and" or "or 2" but not "1 and 2" or "1 or 2"

  [0-9] (' and ' / ' or ') [0-9]  # parses "1 and 2", "1 or 2", etc.

Or repeated subexpressions::

  [0-9] (' and ' [0-9])*  # parses "1", "1 and 2", "3 and 5 and 8", etc.

The three expressions above would translate to the following::

  Choice(Sequence(Class('0-9'), Literal(' and ')), Sequence(Literal(' or '), Class('0-9')))

  Sequence(Class('0-9'), Choice(Literal(' and '), Literal(' or ')), Class('0-9'))

  Sequence(Class('0-9'), Star(Sequence(Literal(' and '), Class('0-9'))))


Optional
--------

``e?``


Star
----

``e*``


Plus
----

``e+``


Bind
----

``n:e``

``:e``

* If the bound expression is repeated (an optional, star, or plus), a
  sequence, or a choice, or indirectly one of these through some chain of
  nonterminals to rules where no rule specifies an action, the associated
  value is the values list;
* Otherwise, if the values list is empty, the associated value is ``None``;
* Otherwise, the associated value is the last item on the values list

.. code::

   # Expression        # Input    # Value of 'a'
   a:.                 # abcd     'a'
   a:"abc"             # abcd     'abc'
   a:[abc]             # abcd     'a'
   a:A                 # abcd     'abc'
   a:B                 # abcd     ['a', 'b', 'c']
   a:.*                # abcd     ['a', 'b', 'c']
   a:(~.*)             # abcd     'abcd'
   a:("a" / A)         # abcd     ['a']
   a:C                 # abcd     'abc'

   # Rules
   A <- "abc"
   B <- "a" "b" "c"
   C <- A


Raw
---

``~e``

https://github.com/PhilippeSigaud/Pegged


Sequence
--------

``e e``


Ordered Choice
--------------

``e / e``

Value Transformations
=====================

.. code::

   # Grammar                        Input  ->  Value
   # -------------------------------------------------------
   Start <- [0-9]                   '3'    ->  '3'
   # -------------------------------------------------------
   Start <- [0-9]          -> int   '3'    ->  0
   # -------------------------------------------------------
   Start <- ([0-9])                 '3'    ->  '3'
   # -------------------------------------------------------
   Start <- ([0-9])        -> int   '3'    ->  3
   # -------------------------------------------------------
   Start <- (([0-9]))      -> int   '3'    ->  *error*
   # -------------------------------------------------------
   Start <- Digit                   '3'    ->  '3'
   Digit <- [0-9]
   # -------------------------------------------------------
   Start <- Digit                   '3'    ->  0
   Digit <- [0-9]          -> int
   # -------------------------------------------------------
   Start <- Digit                   '3'    ->  '3'
   Digit <- ([0-9])
   # -------------------------------------------------------
   Start <- (Digit)                 '3'    ->  '3'
   Digit <- [0-9]
   # -------------------------------------------------------
   Start <- (Digit)                 '3'    ->  0
   Digit <- [0-9]          -> int
   # -------------------------------------------------------
   Start <- Digit                   '3'    ->  3
   Digit <- ([0-9])        -> int


.. code::

   # Grammar                        Input  ->  Value
   Start <- "-" [0-9]               '-3'   ->  '-3'
   # -------------------------------------------------------
   Start <- "-" [0-9]      -> int   '-3'  ->  -3
   # -------------------------------------------------------
   Start <- "-" ([0-9])             '-3'  ->  ['3']
   # -------------------------------------------------------
   Start <- "-" ([0-9])    -> int   '-3'  ->  *error*
   # -------------------------------------------------------
   Start <- "-" Digit               '-3'  ->  '-3'
   Digit <- [0-9]
   # -------------------------------------------------------
   Start <- "-" Digit               '-3'  ->  ['-', 3]
   Digit <- [0-9]          -> int
   # -------------------------------------------------------
   Start <- "-" Digit               '-3'  ->  ['-', ['3']]
   Digit <- ([0-9])
   # -------------------------------------------------------
   Start <- "-" (Digit)             '-3'  ->  ['3']
   Digit <- [0-9]
   # -------------------------------------------------------
   Start <- ("-") (Digit)           '-3'  ->  ['-', ['3']]
   Digit <- ([0-9])
   # -------------------------------------------------------
   Start <- ("-") Digit             '-3'  ->  ['-']
   Digit <- ([0-9])
