# <img src="docs/_static/logo.png" width="60" alt="pe logo" /> Parsing Expressions

## Features

- Scanners match input text
- Combinators
- Parsers


## Syntax Quick Reference

```regex
# comments follow # characters
# whitespace is not significant

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


## Related Projects

- [Lark](https://github.com/lark-parser/lark) (Python)
- [nom](https://github.com/Geal/nom) (Rust)
- [Parsimonious](https://github.com/erikrose/parsimonious) (Python)
