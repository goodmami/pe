# <img src="docs/logo.png" width="60" alt="pe logo" /> Parsing Expressions

**pe** is a library for parsing expressions, including [parsing
expression grammars] (PEGs). It aims to join the expressive power of
parsing expressions with the familiarity of regular expressions.  For
example:

``` python
>>> import pe
>>> m = pe.match(r'["] (!["\\] . / "\\" .)* ["]',
...              '"escaped \\"string\\"" ...')
>>> m.value()
'"escaped \\"string\\""'
```

[parsing expression grammars]: https://en.wikipedia.org/wiki/Parsing_expression_grammar


## Features and Goals

* Grammar notation is backward-compatible with standard PEG
  - Syntactic extensions should be rare
  - Instead, a [specification](docs/specification.md) describes semantic extensions
* Parsers are fast and memory efficient
  - Currently it beats [Lark](https://github.com/lark-parser/lark) at
    the JSON task (caveat: just one test is not representative)
  - The plan is to support C or Cython extensions; [initial
    tests](https://github.com/goodmami/textpy) are promising
* API is intuitive and familiar
  - Modeled on the standard API's `re` module
* Grammar definitions and parser implementations are separate
  - Optimizations target the abstract grammar definitions
  - Multiple parsers are available (currently [packrat](pe/packrat.py)
    for memoizing recursive descent and [machine](pe/machine.py) for
    an iterative "parsing machine" as from [Medeiros and
    Ierusalimschy, 2008].

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

# (extension) raw substring
~e           # result of e is matched substring

# (extension) binding
:e           # discard result after match
name:e       # bind result of e to 'name'

# grammars
Name <- ...  # define a rule named 'Name'
... <- Name  # refer to rule named 'Name'
```

## Matching Inputs with Parsing Expressions

When a parsing expression matches an input, it returns a `Match`
object, which is similar to those of Python's
[re](https://docs.python.org/3/library/re.html) module for regular
expressions. The default value of a match is the substrings the
expression matched.

```python
>>> e = pe.compile(r'[0-9] [.] [0-9]')
>>> m = e.match('1.4')
>>> m.groups()
('1', '.', '4')
>>> m.groupdict()
{}
>>> m.value()
('1', '.', '4')
```

### Value bindings

A value binding takes a sub-match (e.g., of a sequence, choice, or
repetition) and extracts it from the match's value while optionally
associating it with a name that is made available in the
`Match.groupdict()` dictionary.

```python
>>> e = pe.compile(r'[0-9] x:[.] [0-9]')
>>> m = e.match('1.4')
>>> m.groups()
('1', '4')
>>> m.groupdict()
{'x': '.'}
>>> m.value()
('1', '4')
```

### Actions

Actions are functions that are called on a match as follows:

``` python
action(*match.groups(), **match.groupdict())
```

While you can define your own functions that follow this signature,
**pe** provides some helper functions for common operations, such as
`pack(func)`, which packs the `*args` into a list and calls
`func(arglist)`, or `join(func, sep='')` which joins all `*args` into
a string with `sep.join(args)` and calls `func(argstring)`.

The return value of the action becomes the value of the
expression. Note that the return value of `Match.groups()` is always
an iterable while `Match.value()` can return a single object.

```python
>>> from pe.actions import join
>>> e = pe.compile(r'[0-9] [.] [0-9]', action=join(float))
>>> m = e.match('1.4')
>>> m.groups()
(1.4,)
>>> m.groupdict()
{}
>>> m.value()
1.4
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
- [LPeg](http://www.inf.puc-rio.br/~roberto/lpeg/) (Lua)
