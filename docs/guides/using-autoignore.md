
# Ignoring Whitespace by Default

Basic parsing expression grammars (PEGs) do not formally define tokens
separately from other grammar rules, and as such it is not possible to
tell the parser to ignore all tokens of a certain type, such as
whitespace. This is why PEGs often have rules like this (a subset of a
JSON grammar):

```peg
Array    <- LBRACKET Value (COMMA Value)* RBRACKET

LBRACKET <- "[" Spacing
RBRACKET <- "]" Spacing
COMMA    <- "," Spacing
```

Wherever whitespace may occur, it must be defined by the grammar.

As an extension to standard PEG syntax, **pe** allows "autoignore"
rules via the `< ` rule operator (inspired by the [space arrow][] from
the [Pegged][] parser), which transforms the grammar to interleave a
particular pattern around and between sequence items. The above
grammar then becomes:

```peg
Array    <- LBRACKET Value (COMMA Value)* RBRACKET

LBRACKET <- "["
RBRACKET <- "]"
COMMA    <- ","
```

or even:

```peg
Array    <  "[" Value ("," Value)* "]"
```

Only grammar rules that use the `< ` rule operator will use
autoignore. By default, the ignore pattern is
[pe.patterns.DEFAULT_IGNORE](pe.patterns#DEFAULT_IGNORE), but it can be customized by changing the `ignore` parameter when compiling a grammar:

```python
import pe
from pe.operators import Star, Class
g = pe.compile(r"'a' 'b'", ignore=Star(Class(" \t\n\r\v\f")))
```

Currently the value of the `ignore` parameter must be constructed
using [pe.operators](../api/pe.operators.md), but this may change in
the future.

Finally, any semantics in the ignore pattern, such as captures,
bindings, or actions, will be stripped out of the definition so there
is no semantic effect of parsing the ignore pattern.

[space arrow]: https://github.com/PhilippeSigaud/Pegged/wiki/Extended-PEG-Syntax#space-arrow-and-user-defined-spacing
[Pegged]: https://github.com/PhilippeSigaud/Pegged
