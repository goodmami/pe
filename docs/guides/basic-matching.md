
# Matching Strings

This guide covers the basics of matching strings with parsing
expressions. It is assumed that you've imported **pe** as follows:

```python
>>> import pe

```

[pe.match()]: ../api/pe.md#match
[pe.compile()]: ../api/pe.md#compile
[pe.Match]: ../api/pe.md#Match-object
[Match.end()]: ../api/pe.md#Match-end
[Match.group()]: ../api/pe.md#Match-group
[Match.value()]: ../api/pe.md#Match-value
[re]: https://docs.python.org/3/library/re.html
[re.Match]: https://docs.python.org/3/library/re.html#match-objects


## Calling pe.match()

For most parsing tasks you will probably want to use [pe.compile()] to
create a parser from a grammar, but for very simple tasks the
[pe.match()] function is sufficient. This guide will use the
[pe.match()] function to demonstrate a variety of parsing expressions
without having a separate compile step.

Here's an example:

```python
>>> pe.match(r'"abc"', 'abcdef')  # successful matches return Match objects
<Match object; span=(0, 3), match='abc'>
>>> pe.match(r'"abc"', 'xyz')     # failed matches return None
>>>

```


## Match Objects

Similar to Python's [re] module, the result of a match is returned in
an object with attributes and methods for inspecting the result. In
**pe**, the [pe.Match] object behaves very similar to [re.Match]:

```python
>>> m = pe.match(r'sign:(~[-+])? ~[0-9]*', '-12345')
>>> m.start()
0
>>> m.end()
6
>>> m.group()
'-12345'
>>> m.groups()
('12345',)
>>> m.group(1)
'12345'
>>> m.groupdict()
{'sign': '-'}

```

The only difference from [re.Match] to note here is that the bound
value (i.e., named capture) does not appear in the sequence of
groups. For a fuller list of differences between [re] and **pe**, see
the FAQ section on [*how do parsing expressions differ from regular
expressions?*](../faq.md#how-do-parsing-expressions-differ-from-regular-expressions)

In addition, [pe.Match] objects have a [Match.value()] function which
returns the end result of parsing. For parsers that capture values or
insert values from semantic actions, [Match.value()] returns the first
value on the [Match.groups()] sequence. If [Match.groups()] is an
empty sequence, `None` is returned instead.
