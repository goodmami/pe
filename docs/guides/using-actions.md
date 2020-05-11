
# Using Actions

This guide shows you how to transform parsed values with semantic
actions. It assumes you already know how to [match
strings](basic-matching.md) with **pe**.

In **pe**, [Rules](../specification.md#rule) apply semantic actions to
parse results. For an action *func*, the action is applied to the
emitted *args* and bound *kwargs* like this:

``` python
func(*args, **kwargs)
```

The return value of *func* then becomes the only emitted value going
forward and all bound values are cleared. For more advanced usage,
objects of the [pe.actions.Action][Action] class get more context
about a match:

``` python
action(s, pos, end, args, kwargs)
```

Here, *s* is the string the expression is matched against, *pos* and
*end* are the start and end positions of the match, and args and
kwargs are the emitted and bound values. Note that unlike regular
functions, the emitted and bound values are not unpacked for the
call. Also, the result of this call is a tuple and a dictionary that
become the new emitted and bound variables.


[pe.actions]: ../api/pe.actions.md
[Action]: ../api/pe.actions.md#Action
[pe.compile()]: ../api/pe.md#compile
[pe.match()]: ../api/pe.md#match
[pe.Grammar]: ../api/pe.md#Grammar-Objects

## Specifying Actions in Grammars

When compiling a PEG grammar into a parser with [pe.match()] or
[pe.compile()], actions may be set on any named definition with the
*actions* parameter.

```python
>>> import pe
>>> m = pe.match(r'~("0" / [1-9][0-9]*)',
...              '456',
...              actions={'Start': int})
>>> m.group()
'456'
>>> m.value()
456

```

> **Note: Default Start Symbol**
>
> If the grammar given to [pe.match()] or [pe.compile()] is an
> anonymous expression (i.e., it is not assigned to a named
> definition), **pe** will assign it the default name of `Start`

If you are assembling a grammar with the
[pe.operators](../api/pe.operators.md) API, you can define rules
anywhere.

```python
>>> from pe.operators import Class, Star, Capture, Sequence, Choice, Rule
>>> int_expr = Rule(
...     Capture(Choice('0', Sequence(Class('1-9'), Star(Class('0-9'))))),
...     int
... )
>>> int_grammar = pe.Grammar(definitions={'Start': int_expr})
>>> int_parser = pe.compile(int_grammar)
>>> m = int_parser.match('456')
>>> m.group()
'456'
>>> m.value()
456

```

In addition, actions can be specified named definitions in the
[pe.Grammar] object via an *actions* parameter as with [pe.match()]
and [pe.compile()]:

```python
>>> int_expr2 = Capture(Choice('0', Sequence(Class('1-9'), Star(Class('0-9')))))
>>> int_grammar2 = pe.Grammar(definitions={'Start': int_expr2},
...                           actions={'Start': int})
>>> int_parser = pe.compile(int_grammar2)
>>> int_parser.match('456').value()
456

```
