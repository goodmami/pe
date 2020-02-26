# <img src="docs/_static/logo.png" width="60" alt="pe logo" /> Parsing Expressions

**pe** is a library for parsing expressions, including parsing
expression grammars (PEGs). It aims to join the expressive power of
parsing expressions with the familiarity of regular expressions.
For example:

``` python
>>> import pe
>>> m = pe.match(r''' '"' (!["\\] . / '\\' .)* '"' ''',
...              '"escaped \\"string\\"" ...')
>>> m.value()
'"escaped \\"string\\""'
```

## Syntax Quick Reference

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

# extended repetition
e{2}        # exactly two
e{2,5}      # between two and five
e{2:d}      # exactly two delimited by d
e{2,5:d}    # between two and five delimited by d

# combining expressions
e1 e2       # sequence of e1 and e2
e1 | e2     # ordered choice of e1 and e2
(?:e)       # non-capturing group
(e)         # capturing group

# lookahead
&e          # positive lookahead
!e          # negative lookahead

# grammars
Name = ...  # define a rule named 'Name'
... = Name  # refer to rule named 'Name'
```

## Capturing Groups and the Value of Expressions

If an expression has no capturing groups, its value is the substring
it matches. If it has one or more capturing groups, the expression's
value is a list of the values of each group, and anything not in a
group is discarded. Nesting or repeating groups provides even more
options for shaping the value.


| Expression                  | Input    | Value                    |
| --------------------------- | -------- | ------------------------ |
| `"-"? [1-9] [0-9]*`         | `'-123'` | `'-123'`                 |
| `("-"? [1-9] [0-9]*)`       | `'-123'` | `['-123']`               |
| `("-")? [1-9] [0-9]*`       | `'-123'` | `['-']`                  |
| `("-")? [1-9] [0-9]*`       | `'123'`  | `[]`                     |
| `("-"?) [1-9] [0-9]*`       | `'123'`  | `['']`                   |
| `"-"? ([1-9] [0-9]*)`       | `'-123'` | `['123']`                |
| `"-"? ([1-9]) ([0-9]*)`     | `'-123'` | `['1', '23']`            |
| `"-"? ([1-9]) ([0-9])*`     | `'-123'` | `['1', '2'. '3']`        |
| `("-")? (([1-9]) ([0-9])*)` | `'-123'` | `['-', ['1', '2', '3']]` |


## Similar Projects

- [Lark](https://github.com/lark-parser/lark) (Python)
- [nom](https://github.com/Geal/nom) (Rust)
- [Parsimonious](https://github.com/erikrose/parsimonious) (Python)
- [Rosie](https://rosie-lang.org/) (Multiple bindings)
- [TatSu](https://tatsu.readthedocs.io/en/stable/) (Python)
