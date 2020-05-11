
# Frequently Asked Questions


## How Do Parsing Expressions Differ from Regular Expressions?

Parsing expressions are a lot like regular expressions with a few key
differences, as discussed below. For the examples in this section,
import **pe** and [re] as follows:

```python-console
>>> import pe
>>> import re

```

[re]: https://docs.python.org/3/library/re.html

### Backtracking


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

### Recursion

Parsing expressions match recursively using nonterminals and grammars.

```python-console
>>> pe.match(r'Bracketed <- "[" Bracketed "]" / ""', '[[[]]][]')
<Match object; span=(0, 6), match='[[[]]]'>

```


### Captures

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


## Does pe Support Left-Recursion?

No. There is an feature request at
[#11](https://github.com/goodmami/pe/issues/11), but it hasn't been a
priority yet.

**Description**

> Top-down parsers can get stuck in an infinite loop on left-recursive
> grammar definitions, such as the following:
>
> ```peg
> expr <- expr "+" term
> ```
>
> When parsing `expr`, the parser will call `expr` again before
> consuming anything, and this continues infinitely (or until some
> recursion limit is reached). Sometimes left-recursive definitions
> are more natural to write and when parsed (as intended) they provide
> left-associativity (e.g., so `5 - 3 + 2` parses as `(5 - 3) + 2` and
> not `5 - (3 + 2)`).


## Does pe Parse Indentation?

Yes, it can parse whitespace like indentation, but if it is meaningful
(e.g., indentation in Python, YAML, or Markdown) then you'll need to
write an appropriate action to assign the meaning.

**Description**

> PEG by itself is not context-sensitive enough to decide whether some
> line is a child or not of its previous line depending on the indent
> levels of the previous and current lines.  For example, say you want
> to parse Markdown-style lists:
>
> ```markdown
> - one
>   - one.one
>     still one.one
>   - one.two
> - two
> ```
>
> There's currently no way for the parser to decide that the second
> and third bullets belong under the first one and that the last one
> is a sibling of the first. What you would do instead is parse each
> line and capture the indent level, then use an action to group lines
> into blocks.
