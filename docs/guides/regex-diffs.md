
# Differences with Regular Expressions

Parsing expressions are a lot like regular expressions with a few key
differences, as discussed below. For the examples in this section,
import **pe** and [re] as follows:

```python-console
>>> import pe
>>> import re

```

## Backtracking


Parsing expressions has limited backtracking; only prioritized choice
operators (`/`) can backtrack, while others (notably repetition
operators such as start (`*`) and plus (`+`)) are greedy. For
instance, the regular expression `(a|ab)c` and the parsing expression
`("a" / "ab") "c"` are not equivalent, as shown below:

```python-console
>>> re.match(r'(a|ab)c', 'abc').group()
'abc'
>>> pe.match(r'("a" / "ab") "c"', 'abc') is None
True

```

This is because the prioritized choice does not consider alternatives
once one of them succeeds. In order to make the parsing expression
equivalent to the regular expression, the more specific (e.g., longer)
alternatives should be tried first:

```python-console
>>> pe.match(r'("ab" / "a") "c"', 'abc')
<Match object; span=(0, 3), match='abc'>

```

Practically, this means that lookahead assertions are more important.

## Recursion

Parsing expressions match recursively using nonterminals and grammars.

```python-console
>>> pe.match(r'Bracketed <- "[" Bracketed "]" / ""', '[[[]]][]')
<Match object; span=(0, 6), match='[[[]]]'>

```


## Captures

Capturing groups in regular expressions are very similar to **pe**
captures. Both serve to take the substring of matched subexpression
and make it available to the caller, and both allow for indexed or
named captures. One notable difference is that **pe** all captures in
a repetition are emitted instead of just the last one. Compare:

```python-console
>>> re.match(r'([abc]*)', 'aabbcc').groups()   # repetition inside group
('aabbcc',)
>>> re.match(r'([abc])*', 'aabbcc').groups()   # repetition outside group
('c',)
>>> pe.match(r'~[abc]*', 'aabbcc').groups()    # repetition inside group
('aabbcc',)
>>> pe.match(r'(~[abc])*', 'aabbcc').groups()  # repetition outside group
('a', 'a', 'b', 'b', 'c', 'c')

```

Another difference is that named captures (called *bound values* in
**pe**) are no longer available as regular indexed captures:

```python-console
>>> m = re.match(r'(?P<x>[abc]*)', 'aaa')
>>> m.groupdict()
{'x': 'aaa'}
>>> m.groups()
('aaa',)
>>> m = pe.match(r'x:(~[abc]*)', 'aaa')
>>> m.groupdict()
{'x': 'aaa'}
>>> m.groups()
()

```

[re]: https://docs.python.org/3/library/re.html
