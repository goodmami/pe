
# Control Parser Behavior with Flags

The [pe.compile()][], [pe.match()][], and [Parser.match()][] functions
can take a `flags` parameter that can change how the parser is
constructed or applied.

[pe.match()]: ../api/pe.md#match
[pe.compile()]: ../api/pe.md#compile
[Parser.match()]: ../api/pe.md#Parser-match

## Flags for Grammar Construction

When calling [pe.compile()][], the following flags can affect how the
grammar is constructed:

| Flag          | Effect                                                                      |
| ------------- | --------------------------------------------------------------------------- |
| `pe.NONE`     | No flags set                                                                |
| `pe.DEBUG`    | Enable DEBUG mode                                                           |
| `pe.INLINE`   | Inline nonterminals when possible                                           |
| `pe.COMMON`   | Replace common grammar patterns with faster alternatives                    |
| `pe.REGEX`    | Replace expressions with equivalent regular expressions\*                   |
| `pe.OPTIMIZE` | Set all grammar optimization options (`pe.INLINE`, `pe.COMMON`, `pe.REGEX`) |

\* Available for the `packrat` and `machine-python` parsers only.

For instance, the DEBUG mode can show you the effect of optimizations:

```pycon
>>> import pe
>>> grm = r'''
... Start <- Token (" "+ Token)*
... Token <- CHAR+
... CHAR  <- !" " .
... '''
>>> p = pe.compile(grm, flags=pe.DEBUG|pe.INLINE)
## Grammar ##
Start <- Token (" "+ Token)*
Token <- CHAR+
CHAR  <- !" " .
## Modified Grammar ##
Start <- (!" " .)+ (" "+ (!" " .)+)*
Token <- (!" " .)+
CHAR  <- !" " .

```

With the `packrat` parser, the `pe.DEBUG` flag also inserts actions
that print each step of parsing, with the input string context on the
left and the current expression on the right. Expressions are indented
to show nesting levels.

```pycon
>>> p.match('ab c')
ab c         |    (!" " .)+ (" "+ (!" " .)+)*
ab c         |      (!" " .)+
ab c         |        !" " .
ab c         |          !" "
ab c         |            " "
ab c         |          .
b c          |        !" " .
b c          |          !" "
b c          |            " "
b c          |          .
 c           |        !" " .
 c           |          !" "
 c           |            " "
 c           |      (" "+ (!" " .)+)*
 c           |        " "+ (!" " .)+
 c           |          " "+
 c           |            " "
c            |            " "
c            |          (!" " .)+
c            |            !" " .
c            |              !" "
c            |                " "
c            |              .
             |            !" " .
             |              !" "
             |                " "
             |              .
             |        " "+ (!" " .)+
             |          " "+
             |            " "
<Match object; span=(0, 4), match='ab c'>

```

## Flags for Matching

When matching with [pe.match()][] or [Parser.match()][], there are
flags that affect what happens while parsing. Currently these are only
available for the `packrat` parser.

| Flag          | Effect                           |
| ------------- | -------------------------------- |
| `pe.NONE`     | No flags set                     |
| `pe.STRICT`   | Raise an error on parse failures |
| `pe.MEMOIZE`  | Use memoization                  |

Without `pe.STRICT`, a parse failure means that the matching function
returns `None`, but with the flag enabled it raises an exception. If
`pe.MEMOIZE` is also used, it will print the furthest position in the
input that the parser successfully reached.

```pycon
>>> grm = r'''
...   Start  <- (" "* ~(STRING / INT))+ EOF  # match quoted strings or integers
...   STRING <- ["] (!["] .)* ["]
...   INT    <- "-"? ("0" / [1-9] [0-9]*)
...   EOF    <- !.
... '''
>>> pe.match(grm, '"one" 1')  # matches
<Match object; span=(0, 7), match='"one" 1'>
>>> pe.match(grm, '"one" 1 "two')  # missing quotation mark; returns None
>>> pe.match(grm, '"one" 1 "two', flags=pe.STRICT)  # raises exception
Traceback (most recent call last):
  [...]
pe._errors.ParseError: ParseError: failed to parse; use memoization for more details
>>> pe.match(grm, '"one" 1 "two', flags=pe.STRICT|pe.MEMOIZE)
Traceback (most recent call last):
  [...]
pe._errors.ParseError: 
  line 0, character 8
    "one" 1 "two
            ^
ParseError: `(?=(?P<_5>["](?=(?P<_2>(?:[^"])*))(?P=_2)["]|(?:\-)?(?=(?P<_4>0|[1-9](?=(?P<_3>(?:[0-9])*))(?P=_3)))(?P=_4)))(?P=_5)`

```

Some things to note here:
* The error message shows the optimized expression that failed, so it
  doesn't look like the input grammar. This more accurately shows what
  failed, but it's also harder to decipher.
* Showing an accurate position relies on memoization being used close
  to the failure point, but some grammar optimizations can reduce the
  points where memoization can occur. In this case, I leveraged the
  fact that semantic operations (such as captures and actions) and
  recursion can prevent these optimizations and used a capture (`~`) in
  the `Start` rule. Another option is to first compile a grammar
  without optimizations and match using that.


## Flags for Compiling and Compiling

The [pe.match()][] function does not allow you to specify the flags
used for compilation, and it defaults to `pe.OPTIMIZE`. If you want to
specify the grammar-compilation flags *and* the flags used in
matching, you will need to use [pe.compile()][] followed by
[Parser.match()][] on the resulting parser object.
