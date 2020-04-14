
# Parsing Expressions Tutorial


This tutorial assumes you've imported **pe** as follows:

```python
>>> import pe

```

## Matching Strings


```python
>>> pe.match('"abc"', 'abcdef')
<Match object; span=(0, 3), match='abc'>
>>> pe.match('"abc"', 'xyz')  # no match
>>>
```

## Differences with Regular Expressions

Parsing expressions are a lot like regular expressions with a few key
differences, as discussed below. For the examples in this section,
import [re] as follows:

```python
>>> import re

```

### Backtracking


Parsing expressions has limited backtracking; only prioritized choice
operators (`/`) can backtrack, while others (notably repetition
operators such as start (`*`) and plus (`+`)) are greedy. For
instance, the regular expression `(a|ab)c` and the parsing expression
`("a" / "ab") "c"` are not equivalent, as shown below:

```python
>>> re.match(r'(a|ab)c', 'abc').group()
'abc'
>>> pe.match(r'("a" / "ab") "c"', 'abc') is None
True

```

This is because the prioritized choice does not consider alternatives
once one of them succeeds. In order to make the parsing expression
equivalent to the regular expression, the more specific (e.g., longer)
alternatives should be tried first:

```python
>>> pe.match(r'("ab" / "a") "c"', 'abc')
<Match object; span=(0, 3), match='abc'>

```

Practically, this means that lookahead assertions are more important.

### Recursion

Parsing expressions match recursively using nonterminals and grammars.

```python
>>> pe.match(r'Bracketed <- "[" Bracketed "]" / ""', '[[[]]][]')
<Match object; span=(0, 6), match='[[[]]]'>

```




[re]: https://docs.python.org/3/library/re.html
