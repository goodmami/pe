
# API Reference: pe

## Functions

* pe.**<a id="compile" href="#compile">compile</a>**
  (*source, actions=None, parser='packrat', flags=pe.OPTIMIZE*)

  Compile the parsing expression or grammar defined in *source* and
  return the [Parser](#Parser) object. If *source* contains a grammar
  with named rules, the first rule is the starting
  expression. Otherwise if *source* only contains an anonymous
  expression, the expression is associated with the rule name
  `'Start'`.

  The *actions* parameter is used to associate semantic actions to
  grammar rules. Its argument should be a dictionary mapping rule
  names to callables.

  The *parser* argument selects the underlying parser
  implementation. By default this is `'packrat'` for the
  [packrat](pe.packrat.md) *parser*, but it can be set to `"machine"`
  to use the state machine parser.

  The *flags* argument can be used to affect how the parser is
  initialized. By default it is [pe.OPTIMIZE](#OPTIMIZE), but
  [pe.DEBUG](#DEBUG) is useful flag when experimenting. Note that
  changing the flag's value will disable optimization unless the
  [pe.OPTIMIZE](#OPTIMIZE) flag is set again.

  * **Example**

    ```python
    >>> import pe
    >>> float_parser = pe.compile(
    ...     r'''
    ...     Float    <- ~( INTEGER FRACTION? EXPONENT )
    ...     INTEGER  <- '-'? ('0' / [1-9] [0-9]*)
    ...     FRACTION <- '.' [0-9]+
    ...     EXPONENT <- [eE] [-+]? [0-9]+
    ...     ''',
    ...     actions={'Float': float}
    ... )
    >>> m = float_parser.match('0.183e+3')
    >>> m.value()
    183.0

    ```


* pe.**<a id="match" href="#match">match</a>**
  (*pattern, string, actions=None, parser='packrat', flags=pe.MEMOIZE | pe.STRICT*)

  Match the parsing expression defined in *pattern* against the input
  *string*.

  By default the grammar is optimized and the [packrat](pe.packrat.md)
  *parser* is used. The *parser* parameter can be set to `"machine"`
  to use the state machine parser, but for more control over grammar
  compilation use the [compile()](#compile) function.

  The *flags* parameter is used to affect parsing behavior; by default
  it uses [pe.MEMOIZE](#MEMOIZE). Note that changing this value will
  disable memoization unless the [pe.MEMOIZE](#MEMOIZE) flag is set
  again.

  * **Example**

    ```python
    >>> pe.match(r'"-"? ("0" / [1-9] [0-9]*)', '-183')
    <Match object; span=(0, 4), match='-183'>

    ```


* pe.**<a id="escape" href="#escape">escape</a>**
  (*string*)

  Escape any characters in *string* with a special meaning in literals
  or character classes.

  * **Example**

    ```python
    >>> pe.escape('"\n"')
    '\\"\\n\\"'

    ```


* pe.**<a id="unescape" href="#unescape">unescape</a>**
  (*string*)

  Unescape escaped characters in *string*. Characters that are
  unescaped include those that would be escaped by
  [pe.escape](#escape) and also unicode escapes.

  * **Example**

    ```python
    >>> pe.unescape('\\"\\u3042\\"')
    '"あ"'

    ```


## Classes

* *class* pe.**<a id="Parser" href="#Parser">Parser</a>**
  (*grammar, flags=pe.NONE*)

  A generic parser class. This is not meant to be instantiated
  directly, but is used as the superclass for parsers such as
  [PackratParser](pe.packrat.md#PackratParser) and
  [MachineParser](pe.machine.md#MachineParser).


  * **<a id="Parser-match" href="#Parser-match">match</a>**
    (*s, pos=0, flags=pe.NONE*)

    Match the string *s* using the parser.

    The *flags* argument affects parsing behavior, such as with
    [pe.STRICT](#STRICT) or [pe.MEMOIZE](#MEMOIZE).


* *class* pe.**<a id="Match" href="#Match">Match</a>**
  (*string, pos, end, pe, args, kwargs*)

  A match object contains information about a successful match.


  * **<a id="Match-string" href="#Match-string">string</a>**

    The string the expression was matched against.


  * **<a id="Match-pos" href="#Match-pos">pos</a>**

    The position in the string where the match began.


  * **<a id="Match-end" href="#Match-end">end</a>**

    The position in the string where the match ended.


  * **<a id="Match-group" href="#Match-group">group</a>**
    (*key_or_index=0*)

    Return an emitted or bound value given by *key_or_index*, or
    return the entire matching substring when *key_or_index* is `0`
    (default).  When *key_or_index* is an integer greater than 0, it
    is a 1-based index for the emitted value to return. When
    *key_or_index* is a string, it is the name of the bound value to
    return. In either of these last two cases, if the index or name
    does not exist, an IndexError is raised.


  * **<a id="Match-groups" href="#Match-groups">groups</a>**()

    Return the tuple of emitted values.


  * **<a id="Match-groupdict" href="#Match-groupdict">groupdict</a>**()

    Return the dictionary of bound values.


  * **<a id="Match-value" href="#Match-value">value</a>**()

    Return the result of evaluating the input against the expression.


## Exceptions

* *class* pe.**<a id="Error" href="#Error">Error</a>**()

  General error class raised by erroneous **pe** operations.


* *class* pe.**<a id="GrammarError" href="#GrammarError">GrammarError</a>**()

  *Inherits from [pe.Error](#Error).*

  Raised for invalid grammar definitions.


* *class* pe.**<a id="ParseError" href="#ParseError">ParseError</a>**
  (*message=None, filename=None, lineno=None, offset=None, text=None*)

  *Inherits from [pe.Error](#Error).*

  Raised for parsing errors when the [pe.STRICT](#STRICT) flag is set.


## Flags

The following constant values affect grammar compilation or matching
behavior.

* pe.**<a id="NONE" href="#NONE">NONE</a>**

  The flag used when no flags are set.


* pe.**<a id="DEBUG" href="#DEBUG">DEBUG</a>**

  Display debug information when compiling a grammar.


* pe.**<a id="STRICT" href="#STRICT">STRICT</a>**

  Raise an error on parse failures rather than just returning `None`.


* pe.**<a id="MEMOIZE" href="#MEMOIZE">MEMOIZE</a>**

  Use memoization if the parser allows it.


* pe.**<a id="OPTIMIZE" href="#OPTIMIZE">OPTIMIZE</a>**

  Optimize the grammar by inlining some expressions and merging
  adjacent expressions into a single regular expression.
