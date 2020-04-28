
# Common Patterns

This guide lists some common parsing expressions. Feel free to copy
these definition into your grammars, or just use the expressions
directly. Note that some patterns depend on others.

## Whitespace and Boundaries

```peg
EPS         <- ""                       # the empty string (always matches)
EOF         <- !.                       # end-of-file
EOL         <- "\r\n" / [\r\n]          # end-of-line
ToEOF       <- .*                       # everything until the end-of-file
ToEOL       <- !EOL .                   # everything until the end-of-line
WS          <- [\t\n\v\f\r ]            # ASCII whitespace
# Unicode has many more whitespace characters
UNICODEWS   <- [\t\n\v\f\r \x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]
```

##  Numeric

```peg
BIN         <- [01]                     # binary digit
OCT         <- [0-7]                    # octal digit
DEC         <- [0-9]                    # decimal digit
HEX         <- [0-9A-Fa-f]              # hexadecimal digit

DIGITS      <- DEC+                     # decimal digits
UINTEGER    <- "0" / !"0" DIGITS        # unsigned integer
INTEGER     <- "-"? UINTEGER            # signed integer (positive unmarked)
SINTEGER    <- [-+]? UINTEGER           # signed integer

FLOAT       <- INTEGER FRACTION? EXPONENT?
FRACTION    <- "." DIGITS
EXPONENT    <- [Ee] [-+]? DIGITS
```

## Strings

Strings often vary along a few dimensions, such as the boundary
delimiter characters (e.g., `"` or `'`), whether they can span
multiple lines, and whether escaped characters are allowed, and
sometimes whether literal newlines can be escaped. This example is for
single or double quoted strings that can span multiple lines and can
escape either quote character or the backslash. Any other escape
sequences generate a syntax error.

```peg
DQSTRING    <- ["] (!["\\] CHAR)* ["]
SQSTRING    <- ['] (!['\\] CHAR)* [']
STRING      <- DQSTRING / SQSTRING
CHAR        <- "\\" ['"\\]
             / !"\\" .

# Additional character escape sequences
CONTROLCHAR <- "\\" [0abefnrtv]
OCTALESC    <- "\\" OCT (OCT OCT?)?     # between 1 and 3 octal digits
UTF8ESC     <- "\\x" HEX HEX
UTF16ESC    <- "\\u" HEX HEX HEX HEX
UTF32ESC    <- "\\U" HEX HEX HEX HEX HEX HEX HEX HEX
```
