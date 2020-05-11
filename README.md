# <img src="docs/logo.png" width="60" alt="pe logo" /> Parsing Expressions

[![PyPI Version](https://img.shields.io/pypi/v/pe)](https://pypi.org/project/pe)
![Development Status](https://img.shields.io/pypi/status/pe)
![Python Support](https://img.shields.io/pypi/pyversions/pe)
[![Python Package](https://github.com/goodmami/pe/workflows/Python%20package/badge.svg)](https://github.com/goodmami/pe/actions?query=workflow%3A%22Python+package%22)

**pe** is a library for parsing expressions, including [parsing
expression grammars] (PEGs). It aims to join the expressive power of
parsing expressions with the familiarity of regular expressions.  For
example:

``` python
>>> import pe
>>> m = pe.match(r'["] (!["\\] . / "\\" .)* ["]',
...              '"escaped \\"string\\"" ...')
>>> m.group()
'"escaped \\"string\\""'

```

[parsing expression grammars]: https://en.wikipedia.org/wiki/Parsing_expression_grammar

**Quick Links**

* [Documentation](docs/README.md)
  - [Specification](docs/specification.md)
  - [Guides](docs/guides/README.md)
  - [API Documentation](docs/api/README.md)
  - [FAQ](docs/faq.md)
* [Example Parsers](examples/)


## Current Status

Please note that **pe** is very new and is currently *alpha*-level
software. The API or behavior may change significantly as things are
finalized.


## Features and Goals

* Grammar notation is backward-compatible with standard PEG with few extensions
* A [specification](docs/specification.md) describes the semantic
  effect of parsing (e.g., for mapping expressions to function calls)
* Parsers are often faster than other parsing libraries, sometimes by
  a lot; see the [benchmarks]
* The API is intuitive and familiar; it's modeled on the standard
  API's [re] module
* Grammar definitions and parser implementations are separate
  - Optimizations target the abstract grammar definitions
  - Multiple parsers are available (currently [packrat](pe/packrat.py)
    for recursive descent and [machine](pe/machine.py) for an
    iterative "parsing machine" as from [Medeiros and Ierusalimschy,
    2008] and implemented in [LPeg]).

[benchmarks]: https://github.com/goodmami/python-parsing-benchmarks
[re]: https://docs.python.org/3/library/re.html
[Medeiros and Ierusalimschy, 2008]: http://www.inf.puc-rio.br/~roberto/docs/ry08-4.pdf


## Syntax Overview

**pe** is backward compatible with standard PEG syntax and it is
conservative with extensions.

```regex
# terminals
.            # any single character
"abc"        # string literal
'abc'        # string literal
[abc]        # character class

# repeating expressions
e            # exactly one
e?           # zero or one (optional)
e*           # zero or more
e+           # one or more

# combining expressions
e1 e2        # sequence of e1 and e2
e1 / e2      # ordered choice of e1 and e2
(e)          # subexpression

# lookahead
&e           # positive lookahead
!e           # negative lookahead

# (extension) capture substring
~e           # result of e is matched substring

# (extension) binding
name:e       # bind result of e to 'name'

# grammars
Name <- ...  # define a rule named 'Name'
... <- Name  # refer to rule named 'Name'
```

## Matching Inputs with Parsing Expressions

When a parsing expression matches an input, it returns a `Match`
object, which is similar to those of Python's
[re](https://docs.python.org/3/library/re.html) module for regular
expressions. By default, nothing is captured, but the capture operator
(`~`) emits the substring of the matching expression, similar to
regular expression's capturing groups:

```python
>>> e = pe.compile(r'[0-9] [.] [0-9]')
>>> m = e.match('1.4')
>>> m.group()
'1.4'
>>> m.groups()
()
>>> e = pe.compile(r'~([0-9] [.] [0-9])')
>>> m = e.match('1.4')
>>> m.group()
'1.4'
>>> m.groups()
('1.4',)

```

### Value Bindings

A value binding extracts the emitted values of a match and associates
it with a name that is made available in the `Match.groupdict()`
dictionary. This is similar to named-capture groups in regular
expressions, except that it extracts the emitted values and not the
substring of the bound expression.

```python
>>> e = pe.compile(r'~[0-9] x:(~[.]) ~[0-9]')
>>> m = e.match('1.4')
>>> m.groups()
('1', '4')
>>> m.groupdict()
{'x': '.'}

```

### Actions

Actions (also called "semantic actions") are callables that transform
parse results. When an arbitrary function is given, it is called as
follows:

``` python
func(*match.groups(), **match.groupdict())
```

The result of this function call becomes the only emitted value going
forward and all bound values are cleared.

For more control, **pe** provides the [Action] class and a number of
subclasses for various use-cases. These actions have access to more
information about a parse result and more control over the
match. For example, the [Pack] class takes a function and calls it
with the emitted values packed into a list:

``` python
func(match.groups())
```

And the [Join] class joins all emitted strings with a separator:

``` python
func(sep.join(match.groups()), **match.groupdict())
```

[Action]: docs/api/pe.actions.md#Action
[Pack]: docs/api/pe.actions.md#Pack
[Join]: docs/api/pe.actions.md#Join


### Example

Here is one way to parse a list of comma-separated integers:

```python
>>> from pe.actions import Pack
>>> p = pe.compile(
...   r'''
...     Start  <- "[" Values? "]"
...     Values <- Int ("," Int)*
...     Int    <- ~( "-"? ("0" / [1-9] [0-9]*) )
...   ''',
...   actions={'Values': Pack(list), 'Int': int})
>>> m = p.match('[5,10,-15]')
>>> m.value()
[5, 10, -15]

```

## Similar Projects

- [Lark](https://github.com/lark-parser/lark) (Python)
- [nom](https://github.com/Geal/nom) (Rust)
- [Parsimonious](https://github.com/erikrose/parsimonious) (Python)
- [Rosie](https://rosie-lang.org/) (Multiple bindings)
- [TatSu](https://tatsu.readthedocs.io/en/stable/) (Python)
- [PEG.js](https://github.com/pegjs/pegjs) (Javascript)
- [Pegged](https://github.com/PhilippeSigaud/Pegged) (D)
- [pegen](https://github.com/gvanrossum/pegen) (Python / C)
- [LPeg] (Lua)

[LPeg]: http://www.inf.puc-rio.br/~roberto/lpeg/
