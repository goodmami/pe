# <img src="docs/logo.png" width="60" alt="pe logo" /> Parsing Expressions

**pe** is a library for parsing expressions, including parsing
expression grammars (PEGs). It aims to join the expressive power of
parsing expressions with the familiarity of regular expressions.
For example:

``` python
>>> import pe
>>> m = pe.match(r'["] (!["\\] . / "\\" .)* ["]',
...              '"escaped \\"string\\"" ...')
>>> m.value()
'"escaped \\"string\\""'
```


## Syntax Quick Reference

**pe** is backward compatible with standard PEG syntax and it is
conservative with extensions.

```regex
# basic terms
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

# combining expressions
e1 e2       # sequence of e1 and e2
e1 | e2     # ordered choice of e1 and e2
(e)         # subexpression

# lookahead
&e          # positive lookahead
!e          # negative lookahead

# (extension) binding
:e          # discard result after match
name:e      # bind e to name

# grammars
Name = ...  # define a rule named 'Name'
... = Name  # refer to rule named 'Name'
```

## Matching Inputs with Parsing Expressions

When a parsing expression matches an input, it returns a `Match`
object, which is similar to those of Python's
[re](https://docs.python.org/3/library/re.html) module for regular
expressions. The default value of a match is the substring the
expression matched.

```python
>>> e = pe.compile(r'[0-9] [.] [0-9]')
>>> m = e.match('1.4')
>>> m.groups()
['1.4']
>>> m.groupdict()
{}
>>> m.value()
'1.4'
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
['1', '4']
>>> m.groupdict()
{'x': '.'}
>>> m.value()
'1'
```

### Actions

Actions are functions that are called on a match as follows:

``` python
action(*match.groups(), **match.groupdict())
```

The return value of the action becomes the value of the expression.

```python
>>> e = pe.compile(r'[0-9] :[.] [0-9]',
...                action=lambda a, b: (int(a), int(b)))
>>> m = e.match('1.4')
>>> m.groups()
[(1, 4)]
>>> m.groupdict()
{}
>>> m.value()
(1, 4)
```

## Similar Projects

- [Lark](https://github.com/lark-parser/lark) (Python)
- [nom](https://github.com/Geal/nom) (Rust)
- [Parsimonious](https://github.com/erikrose/parsimonious) (Python)
- [Rosie](https://rosie-lang.org/) (Multiple bindings)
- [TatSu](https://tatsu.readthedocs.io/en/stable/) (Python)
- [PEG.js](https://github.com/pegjs/pegjs) (Javascript)
- [Pegged](https://github.com/PhilippeSigaud/Pegged) (D)
