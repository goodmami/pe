
# Matching Strings

This guide assumes you've imported **pe** as follows:

```python
>>> import pe

```

```python
>>> pe.match('"abc"', 'abcdef')
<Match object; span=(0, 3), match='abc'>
>>> pe.match('"abc"', 'xyz')  # no match
>>>
```

