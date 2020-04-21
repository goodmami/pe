
# API Reference: pe.actions

## Classes

* *class* pe.actions.**<a id="Action" href="#Action">Action</a>**()

  Base class for all semantic actions. Not meant to be used directly.

  Each action used when parsing is an instance of a subclass of
  [Action](#Action). If a user provides a grammar with an action that
  is not such an instance, it must be a callable and it will be
  wrapped in a [Call](#Call) instance.

  Custom actions may be created by subclassing [Action](#Action) and
  defining a [__call__] method as follows:

  ```python
  class MyAction(Action):
      def __call__(self,
	               s: str,
				   pos: int,
				   end: int,
				   value: Value,
				   args: Tuple,
				   kwargs: Dict) -> Tuple[Tuple, Dict]:
	      ...
		  return myargs, mykwargs
  ```

  The *s* parameter is for the string being parsed, while *pos* and
  *end* are for the starting and ending positions of the match in *s*.

  The *value* parameter is a flag indicating the [value type] of the
  expression. Currently this is only used internally for the
  [Bind](#Bind) action.

  The *args* and *kwargs* parameters are for the tuple of emitted
  values and dictionary of bound values, respectively.

  The return values *myargs* and *mykwargs* are the tuple of emitted
  values and dictionary of bound values returned by the
  expression. Normally *myargs* will have one element and *mykwargs*
  is empty, but both are returned to accommodate custom action types.

  These parameter names will be reused below to describe the behavior
  of the actions.

[value-type]: ../specification.md#value-types


* *class* pe.actions.**<a id="Call" href="#Call">Call</a>**()
  (*func*)

  Call *func* with the emitted and bound values as follows:

  ```python
  func(*args, **kwargs)
  ```

  This class is useful for functions that take zero or more arguments
  and possibly keyword arguments. For example, when constructing a
  [datetime] object from integer components.


* *class* pe.actions.**<a id="Pack" href="#Pack">Pack</a>**()
  (*func*)

  Call *func* with the emitted values packed as a tuple and the bound
  values as follows:

  ```python
  func(args, **kwargs)
  ```

  This class is useful for functions that take exactly one iterable
  argument, possibly with keyword arguments, such as [list] or [dict].


* *class* pe.actions.**<a id="Bind" href="#Bind">Bind</a>**()
  (*name*)

  Bind the evaluated emitted values to *name* as follows:

  ```python
  mykwargs[name] = evaluate(args, value)
  ```

  Binding is useful for functions that obligatorily take keyword
  arguments and occasionally for mapping arguments to functions where
  the argument order is different than the parsing order.


* *class* pe.actions.**<a id="Raw" href="#Raw">Raw</a>**()
  (*func*)

  Call *func* with the substring as its only argument as follows:

  ```python
  func(s[pos:end])
  ```

  This action always takes the full substring between *pos* and *end*
  and ignores any values emitted or bound by subexpressions. This
  contrasts with [Join](#Join), which combines only emitted string
  values and includes bound values.


* *class* pe.actions.**<a id="Join" href="#Join">Join</a>**()
  (*func, sep=''*)

  Call *func* with the string formed by joining all emitted values
  with *sep*. This assumes that all emitted values are strings.

  ```python
  func(sep.join(args), **kwargs)
  ```

  This action is useful for filtering out substrings, such as for
  escaped newlines in multiline strings as in Python or [TOML]. Also,
  unlike [Raw](#Raw), this action passes any bound values to *func*.


* *class* pe.actions.**<a id="Constant" href="#Constant">Constant</a>**
  (*value*)

  Return *value*.

  Occasionally the presence of a match is enough to emit a value but
  the content of the match is irrelevant. This action always emits
  *value* if the expression succeeds.


* *class* pe.actions.**<a id="Getter" href="#Getter">Getter</a>**()
  (*i*)

  Return the *i*th emitted value.

  All other emitted and bound values are discarded.


* *class* pe.actions.**<a id="Fail" href="#Fail">Fail</a>**()
  (*message*)

  Raise a [ParseError](pe.md#ParseError) immediately.


[__call__]: https://docs.python.org/3/reference/datamodel.html#object.__call__
[list]: https://docs.python.org/3/library/stdtypes.html#dict
[dict]: https://docs.python.org/3/library/stdtypes.html#list
[datetime]: https://docs.python.org/3/library/datetime.html#datetime.datetime
