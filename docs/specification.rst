
=============
Specification
=============


Quick Reference
===============

.. code:: ruby

   # The following abbreviations are used below:
   #   e - a parsing expression
   #   p - a primary term
   #   q - a quantified term
   #   v - an evaluated term
   #   s - a sequence
   #   A - a nonterminal identifier
   #   n - a binding identifier
   #   $x - the value of x
   #   %x - the bindings of x
   #   ~x - the substring matched by x

   # Op        Name      Type  Matches                      Values        Bindings

   ### Primary Terms
     .       # Dot       p     any single character         [~.]          {}
     "abc"   # Literal   p     the string 'abc'             [~'abc']      {}
     'abc'   # Literal   p     the string 'abc'             [~'abc ]      {}
     [abc]   # Class     p     any one character in 'abc'   [~[abc]]      {}
     A       # Symbol    p     rule A                       $A            {%A}
     (e)     # Group     p     parsing expression e         $e            {%e}

   ### Quantified Terms (repetition)
     p       #           q     primary term p exactly once  $p            {%p}
     p?      # Optional  q     p zero or one times          [] or $p      {} or {%p}
     p*      # Star      q     p zero or more times         [] + $p ...   {} or {%p, ...}
     p+      # Plus      q     p one or more times          $p + $p ...   {%p, ...}

   ### Evaluated Terms
     q       #           v     quantified term q            $q            {%q}
     &q      # And       v     q, but consume no input      []            {}
     !q      # Not       v     not q, but consume no input  []            {}
     n:q     # Bind      v     q                            []            {n:$q}  (see note)
     :q      # Bind      v     q                            []            {}
     ~q      # Raw       v     q                            [~q]          {}

   ### Sequences
     v       #           s     evaluated term v             $v            {%v}
     v s     # Sequence  s     v then sequence s            $v + $s       {%v} + {%s}

   ### Choices
     s       #           e     sequence s                   $s            {%s}
     s / e   # Choice    e     e only if s failed           $s or $e      {%s} or {%e}

   ### Grammars
     A <- e  # Rule      -     parsing expression e         $e            {}
     A <~ e  # Raw       -     parsing expression e         [~e]          {}

* *Note* -- the exact value used in a binding depends on the type of bound
  expression; see below.

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

===========  ========  ==========
Operator     Name      Precedence
===========  ========  ==========
``.``        Dot       5
``" "``      Literal   5
``[ ]``      Class     5
``Abc``      Name      5
``(e)``      Group     5
``e?``       Optional  4
``e*``       Star      4
``e+``       Plus      4
``&e``       And       3
``!e``       Not       3
``:e``       Bind      3
``~e``       Raw       3
``e1 e2``    Sequence  2
``e1 / e2``  Choice    1
===========  ========  ==========


Semantic Values
===============

The value of each expression is a list. For 


Expressions
===========

This document defines the expressions available to **pe**.

Dot
---

``.``


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
