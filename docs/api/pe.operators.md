
# API Reference: pe.operators

## Classes

* *class* pe.operators.**<a id="SymbolTable" href="#SymbolTable">SymbolTable</a>**
  (*op, args*)

  The SymbolTable class is only to assist with the programmatic
  construction of a grammar. As such, it has a very narrow usage
  pattern. Setting a value on an attribute associates the value (an
  expression of operators) with the attribute name. Regular attribute
  access always returns a [Nonterminal](#Nonterminal) operator with
  the attribute name, whether or not an expression is associated with
  the name. The SymbolTable object can then be passed when
  initializing a [Grammar](pe.md#Grammar) object as if a standard
  dictionary had been passed. In otherwords, both `g1` and `g2` below
  are equivalent:

  ```python
  from pe import Grammar
  from pe.operators import SymbolTable, Optional, Capture, Sequence

  g1 = Grammar(definitions={
    'Float': Capture(
        Sequence(Nonterminal('INTEGER'),
                 Optional(Nonterminal('FRACTION')),
                 Optional(Nonterminal('EXPONENT')))),
    'INTEGER': ...,
    'FRACTION': ...,
    'EXPONENT': ...,
  })

  V = SymbolTable()
  V.Float = Capture(
      Sequence(V.INTEGER,
               Optional(V.FRACTION),
               Optional(V.EXPONENT)))
  V.INTEGER = ...
  V.FRACTION = ...
  V.EXPONENT = ...
  g2 = Grammar(definitions=V)
  ```

## Operator Functions

Aside from the [Regex](#Regex) and [Debug](#Debug) operators below,
the rest are described by the [specification](../specification.md).


* pe.operators.**<a id="Dot" href="#Dot">Dot</a>**()

* pe.operators.**<a id="Literal" href="#Literal">Literal</a>**
  (*string*)

* pe.operators.**<a id="Class" href="#Class">Class</a>**
  (*chars*)

* pe.operators.**<a id="Regex" href="#Regex">Regex</a>**
  (*pattern, flags=0*)

  Describe a regular expression as a **pe** operator. The operator
  behaves as other terminals, namely that it has an
  [empty](../specification.md#empty) value type. When parsing, if the
  operator leads to a match, only the matching substring of the
  regular expression is considered; capturing groups are ignored.

* pe.operators.**<a id="Sequence" href="#Sequence">Sequence</a>**
  (*\*expressions*)

* pe.operators.**<a id="Choice" href="#Choice">Choice</a>**
  (*\*expressions*)

* pe.operators.**<a id="Optional" href="#Optional">Optional</a>**
  (*expression*)

* pe.operators.**<a id="Star" href="#Star">Star</a>**
  (*expression*)

* pe.operators.**<a id="Plus" href="#Plus">Plus</a>**
  (*expression*)

* pe.operators.**<a id="Repeat" href="#Repeat">Repeat</a>**
  (*expression, count=-1, min=0, max=-1*)

* pe.operators.**<a id="Nonterminal" href="#Nonterminal">Nonterminal</a>**
  (*name*)

* pe.operators.**<a id="And" href="#And">And</a>**
  (*expression*)

* pe.operators.**<a id="Not" href="#Not">Not</a>**
  (*expression*)

* pe.operators.**<a id="Capture" href="#Capture">Capture</a>**
  (*expression*)

* pe.operators.**<a id="Bind" href="#Bind">Bind</a>**
  (*expression, name*)

* pe.operators.**<a id="Rule" href="#Rule">Rule</a>**
  (*expression, action, name='\<anonymous\>'*)

* pe.operators.**<a id="Debug" href="#Debug">Debug</a>**
  (*expression*)

  Match *expression* and return its results unchanged, but print a
  message to indicate that the operation has occurred. When all other
  operators are wrapped in [Debug](#Debug) operators, the concrete
  syntax tree of a parse is displayed, at the cost of
  performance. This operator is not generally meant to be used
  manually and it has no representation in the grammar notation, but
  rather it is inserted semi-automatically by compiling a grammar with
  the [pe.DEBUG](pe.md#DEBUG) flag.

* pe.operators.**<a id="AutoIgnore" href="#AutoIgnore">AutoIgnore</a>**
  (*expression*)

  Interleave the "ignore" pattern around and between sequence items.
  The ignore pattern is passed to the parser and defaults to
  [pe.patterns.DEFAULT_IGNORE](pe.patterns#DEFAULT_IGNORE).
