# Specification

The **pe** grammar specification extends the [PEG][] syntactic
specification with a description of the semantic effect of parsing.
Any **pe** grammar without extended features or rule actions should
parse exactly as a standard PEG grammar.

## Quick Reference

```julia
# Operator  Name      Value     Description

### Primary Terms (p)
  .       # Dot       Monadic   Match any single character
  'abc'   # Literal   Monadic   Match the string 'abc'
  "abc"   # Literal   Monadic   Match the string 'abc'
  [abc]   # Class     Monadic   Match any one character in 'abc'
  A       # Symbol    Deferred  Match the expression in rule A
  (e)     # Group     Deferred  Match the subexpression e

### Quantified Terms (q)
  p       #           Deferred  Match primary term p exactly once
  p?      # Optional  Variadic  Match p zero or one times
  p*      # Star      Variadic  Match p zero or more times
  p+      # Plus      Variadic  Match p one or more times

### Value-changing Terms (v)
  q       #           Deferred  Match quantified term q
  &q      # And       Niladic   Succeed if q matches; consume no input; return no value
  !q      # Not       Niladic   Fail if q matches; consume no input; return no value
  name:q  # Bind      Niladic   Match q and bind its value to 'name'
  :q      # Bind      Niladic   Match q and discard its value

### Sequences (s)
  v       #           Deferred  evaluated term v
  v s     # Sequence  Variadic  v then sequence s

### Choices (e)
  s       #           Deferred  sequence s
  s / e   # Choice    Variadic  e only if s failed

### Grammars (r)
  A <- e  # Rule      Deferred  parsing expression e
```


## Expression Value Types

- Niladic: expression emits no value
- Monadic: expression always emits a single value
- Variadic: expression emits any number (zero or more) values
- Deferred: value type depends on a resolved expression

Note that the *variadic* type is a generalization which defines an
expression's behavior in **pe**; some expressions always emit one or
more value while some always emit a fixed number. A *monadic*
expression (e.g., `[ab]`) may therefore behave differently from a
*variadic* expression with a single value (e.g., `'a' / 'b'`).


## Grammar Syntax

The following is a formal description of **pe**'s PEG syntax describing
itself. This PEG is based on Bryan Ford's original
[paper][PEG].


```julia
# Hierarchical syntax
Start      <- :Spacing (Expression / Grammar) :EndOfFile
Grammar    <- Definition+
Definition <- Identifier :Operator Expression
Operator   <- Spacing LEFTARROW
Expression <- Sequence (SLASH Sequence)*
Sequence   <- Evaluated*
Evaluated  <- Prefix? Quantified
Prefix     <- AND / NOT / Binding
Binding    <- Identifier? ':' :Spacing
Quantified <- Primary Quantifier?
Quantifier <- QUESTION / STAR / PLUS
Primary    <- Name / Group / Literal / Class / DOT
Name       <- Identifier :Spacing !Operator
Group      <- :OPEN Expression :CLOSE

# Lexical syntax
Identifier <- IdentStart IdentCont*
IdentStart <- [a-zA-Z_]
IdentCont  <- IdentStart / [0-9]

Literal    <- :['] ~( !['] Char )* :['] :Spacing
            / :["] ~( !["] Char )* :["] :Spacing

Class      <- :'[' ~( !']' Range )* :']' :Spacing
Range      <- Char '-' Char / Char
Char       <- '\\' . / .

LEFTARROW  <- '<-' :Spacing
SLASH      <- '/' :Spacing
AND        <- '&' :Spacing
NOT        <- '!' :Spacing
QUESTION   <- '?' :Spacing
STAR       <- '*' :Spacing
PLUS       <- '+' :Spacing
OPEN       <- '(' :Spacing
CLOSE      <- ')' :Spacing
DOT        <- '.' :Spacing

Spacing    <- (Space / Comment)*
Comment    <- '#' (!EndOfLine .)* EndOfLine
Space      <- ' ' / '\t' / EndOfLine
EndOfLine  <- '\r\n' / '\n' / '\r'
EndOfFile  <- !.
```


## Operator Precedence

| Operator         | Name     | Precedence | Expression Type |
| ---------------- | -------- | ---------- | --------------- |
| `.`              | Dot      | 5          | Primary         |
| `" "` or `' '`   | Literal  | 5          | Primary         |
| `[ ]`            | Class    | 5          | Primary         |
| `Abc`            | Name     | 5          | Primary         |
| `(e)`            | Group    | 5          | Primary         |
| `e?`             | Optional | 4          | Quantified      |
| `e*`             | Star     | 4          | Quantified      |
| `e+`             | Plus     | 4          | Quantified      |
| `&e`             | And      | 3          | Evaluated       |
| `!e`             | Not      | 3          | Evaluated       |
| `:e` or `name:e` | Bind     | 3          | Evaluated       |
| `e1 e2`          | Sequence | 2          | Sequence        |
| `e1 / e2`        | Choice   | 1          | Expression      |
| `Abc <- e`       | Rule     | 0          | Rule            |


## Semantic Values


## Preliminaries


### Identifiers

All identifiers (rule and binding names) are limited to the ASCII
letters (`a` through `z` and `A` through `Z`), ASCII digits (`0`
through `9`), and the ASCII underscore (`_`). In addition, the first
character may not be a digit. Identifiers must be one or more of these
characters.


### Special Punctuation

The following ASCII punctuation characters, in addition to
[whitespace](#whitespace), have special meaning in expressions (but
not necessarily inside [string literals](#literal) or [character
classes](#class); for these see below):

    ! " # & ' ( ) * + - . / : ? [ \ ] _

Special characters inside [string literals](#literal) and [character
classes](#class) are different. For both, the `\` character is used
for [escape sequences](#escape-sequences), and therefore it must be
escaped for the literal character. In addition, the following must be
escaped:

- `'` in single-quoted string literals
- `"` in double-quoted string literals
- `[` and `]` inside character classes, as well as `-` in most
  positions

The other ASCII punctuation characters are currently unused but are
reserved in expressions for potential future uses:

    $ % , ; < = > @ ` { | } ~


### Whitespace

Whitespace, including the space, tab, and newline characters (which
include `\n`, `\r`, and `\r\n` sequences) are only significant in
in some contexts:

* To delimit terms in a [sequence](#sequence).
* To terminate a [comment](#comments).
* To distinguish a [binding](#bind) identifier from a
  [nonterminal](#nonterminal) identifier.
* As their literal value inside [string literals](#literal) or
  [character classes](#class).


### Characters

Characters in **pe** are unicode code-points and not bytes, so for
instance the [dot](#dot) operator consumes a single unicode code-point
and not a single byte. [Escape sequences](#escape-sequences) of two or
more ASCII characters in an expression match a single unicode
character in the input. In **pe**, any character that is not allowed
by [identifiers](#identifiers), [special
punctuation](#special-punctuation), or [whitespace](#whitespace) must
occur in a [string literals](#literal) or [character classes](#class).


### Comments

Comments may occur anywhere outside of [string literals](#literal) and
[character classes](#class). They begin with the ASCII `#` character
and continue until the end of the line.


### Escape Sequences

The `\` character is used inside [string literals](#literal) and
[character classes](#class) for escape sequences. These allow one to
use [special punctuation](#special-punctuation) characters for their
literal values or to use unicode code-point encodings. The following
escape sequences or schemes are allowed:

- `\t`: horizontal tab
- `\n`: newline (line feed)
- `\v`: vertical tab
- `\f`: form feed
- `\r`: carriage return
- `\N`, `\NN`, `\NNN`: octal sequence of one to three octal digits; the
  maximum value is `\777`; leading zeros are permitted; the value
  denotes a unicode character and not a byte
- `\xNN`: UTF-8 character sequence of exactly 2 hexadecimal digits
- `\uNNNN`: UTF-16 character sequence of exactly 4 hexadecimal digits
- `\UNNNNNNNN`: UTF-32 character sequence of exactly 8 hexadecimal
  digits
- `\c`: literal character `c` for all characters that are not in the
  set `t n v f r 0 1 2 3 4 5 6 7 x u U`; this includes escape
  sequences such as `\"`, `\'`, `\[`, `\]`, `\-`, and `\\`

Note that for UTF-8 and UTF-16, a single code-point may require more
than one escape sequence. For all others, one escape sequence
corresponds to a single character.

## Expressions

This document defines the expressions available to **pe**.

### Dot

- Notation: `.`
- Function: Dot()
- Type: **Primary**
- Value: **Monadic**

The Dot operator always succeeds if there is any remaining input and
fails otherwise. It consumes a single [character](#characters) and
emits the same character as its value.


### Literal

- Notation: `'abc'` or `"abc"`
- Function: Literal(*string*)
- Type: **Primary**
- Value: **Monadic**

A Literal operator (also called a *string literal* or *string*)
succeeds if the input at the current position matches the given string
exactly and fails otherwise. It consumes input equal in amount to the
length of the given string and the string is emitted as its value.

The `'`, `"`, and `\` characters are special inside a string and must
be [escaped](#escape-sequences) if they are used literally, however
the `'` character may be used unescaped inside a double-quoted string
(e.g, `"'"`) and the `"` character may be used unescaped inside a
single-quoted string (e.g., `'"'`).

Note that newlines do not need to be escaped but doing so can make an
expression more explicit and, thus, more clear.


### Class

- Notation: `[abc]`
- Function: Class(*ranges*)
- Type: **Primary**
- Value: **Monadic**

The Class operator (also called a *character class*) succeeds if the
next [character](#characters) of input is in a set of characters
defined by the given character ranges. It fails if the next character
is not in the set or if there is no remaining input. On success, it
consumes one character of input and emits the same character as its
value.

Each range is either one (possibly [escaped](#escape-sequences))
character or two (possibly escaped) characters separated by `-`. In
the former case, the range consists of the single character. In the
latter case, the range consists of the character before the `-`, the
character after the `-`, and all characters that occur between these
two in the unicode tables. The set of characters used by the class is
the union of all ranges.

It is invalid if a range separated by `-` has a first character with a
value higher than the second character.

The `[`, `]`, `-`, and `\` characters are special inside a character
class and must be escaped if they are used literally, however the `-`
character may be used unescaped if it is the first character in the
range (e.g., `[-abc]`).


### Nonterminal

- Notation: `Abc`
- Function: Nonterminal(*name*)
- Type: **Primary**
- Value: **Deferred**

A Nonterminal operator is given by an [identifier](#identifiers) in an
expression. It corresponds to a grammar [rule](#rule) of the same
name. A nonterminal operator succeeds if, at the current position in
the input, the expression of the named grammar rule succeeds at the
same position. Similarly, it fails if the grammar rule fails at the
same position. The value type of the nonterminal and whether or not it
consumes input are defined by the corresponding grammar rule.

In all cases, the behavior of the nonterminal is the same as if the
corresponding rule's expression had been written in place of the
nonterminal. Schematically, that means that `A1` and `A2` below are
equivalent for any expression `e`.

```julia
A1 <- B
B  <- e

A2 <- (e)
```


### Group

- Notation: `(e)`
- Function: none
- Type: **Primary**
- Value: **Deferred**

Groups do not actually refer to a construct in **pe**, but they are used
to aid in the parsing of a grammar. This is helpful when one wants to
apply a lower-precedence operator with a higher-precedence one, such as
a sequence of choices:

    [0-9] '+' / '-' [0-9]    # parses "1+" or "-2" but not "1+2" or "1-2"

    [0-9] ('+' / '-') [0-9]  # parses "1+2", "1-2", etc.

Or repeated subexpressions:

    [0-9] ('+' [0-9])*  # parses "1", "1+2", "3+5+8", etc.

In the API, the three expressions above would translate to the
following function calls:

    Choice(Sequence(Class('0-9'), Literal('+')), Sequence(Literal('-'), Class('0-9')))

    Sequence(Class('0-9'), Choice(Literal('+'), Literal('-')), Class('0-9'))

    Sequence(Class('0-9'), Star(Sequence(Literal('+'), Class('0-9'))))


### Optional

- Notation: `e?`
- Function: Optional(*expression*)
- Type: **Quantified**
- Value: **Variadic**

The Optional operator succeeds whether the given expression succeeds
or fails. If the given expression succeeds, the emitted value and
consumed input is the same as that of the given expression. If the
given expression fails, no input is consumed and no value is emitted.

Note that the Optional operator also succeeds when there is no
remaining input.


### Star

- Notation: `e*`
- Function: Star(*expression*)
- Type: **Quantified**
- Value: **Variadic**

The Star operator succeeds if the given expression succeeds zero or
more times. The accumulated values of the given expression are
emitted.

Note that the Star operator also succeeds when there is no remaining
input.


### Plus

- Notation: `e+`
- Function: Plus(*expression*)
- Type: **Quantified**
- Value: **Variadic**

The Plus operator succeeds if the given expression succeeds one or
more times. The accumulated values of the given expression are
emitted.


### And

- Notation: `&e`
- Function: And(*expression*)
- Type: **Evaluated**
- Value: **Niladic**

The And operator (also called *positive lookahead*) succeeds when the
given expression succeeds at the current position in the input, but no
input is consumed (even though the given expression would otherwise
consume input) and no values are emitted.


### Not

- Notation: `!e`
- Function: Not(*expression*)
- Type: **Evaluated**
- Value: **Niladic**

The Not operator (also called *negative lookahead*) succeeds when the
given expression fails at the current position in the input, but no
input is consumed and no values are emitted.


### Bind

- Notation: `:e` or `name:e`
- Function: Bind(*expression*, *name*=None)
- Type: **Evaluated**
- Value: **Niladic**

The Bind operator succeeds when the given expression succeeds at the
current line of input, but no values are emitted. Unlike the
[And](#and) operator, matching input is consumed. If a name is given,
the value of the given expression is associated with the name for the
duration of a rule.

The bound value depends on the value type of the bound expression:

- Niladic: `None`
- Monadic: the value emitted by the monadic expression
- Variadic: the sequence of values emitted by the variadic expression

```julia
# Expression        # Input    # Value of 'a'
a:.                 # abcd     'a'
a:"abc"             # abcd     'abc'
a:[abc]             # abcd     'a'
a:A                 # abcd     'abc'
a:B                 # abcd     ['a', 'b', 'c']
a:.*                # abcd     ['a', 'b', 'c']
a:("a" / A)         # abcd     ['a']
a:C                 # abcd     'abc'

# Rules
A <- "abc"
B <- "a" "b" "c"
C <- A
```

### Sequence

- Notation: `e e`
- Function: Sequence(*expression*, ...)
- Type: **Sequence**
- Value: **Variadic**

The Sequence operator succeeds when all of its given expressions
succeed, in turn, from the current position in the input. After an
expression succeeds, possibly consuming input, successive expressions
start matching at the new position in the input, and so on. The
Sequence operator emits the accumulated values of its given
expressions. If any given expression fails, the entire Sequence fails
and no values are emitted and no input is consumed.

A Sequence with no given expressions is invalid. A Sequence with one
given expression is reduced to the given expression only.


### Choice

- Notation: `e / e`
- Function: Choice(*expression*, ...)
- Type: **Expression**
- Value: **Variadic**

The Choice operator succeeds when any of its given expressions
succeeds. If a given expression fails, the next given expression is
attempted at the current position in the input. If a given expression
succeeds, the Choice operator succeeds and immediately emits the given
expression's value and consumes its input.

A Choice with no given expressions is invalid. A Choice with one given
expression is reduced to the given expression only.


### Rule

- Notation: `Abc <- e`
- Function: Rule(*expression*, *action*=None)
- Type: **Rule**
- Value: **Deferred**

A Rule is often associated with a name in the grammar, but the rule
itself is just a wrapper around a given expression that provides some
additional behavior. The rule thus succeeds when the given expression
succeeds, emitting the given expressions value and consuming its
input. If an action is defined, the value type of the rule is
*monadic* and it emits the result of applying the action with any
emitted or bound values. If no action is defined, the value type of
the Rule is the resolved value type of the given expression. After the
rule completes, any bound values are cleared, regardless of whether an
action was defined.

Note that, while Rules may only be defined in the PEG notation with a
name in the grammar, anonymized rules may appear inside of
expressions. This situation can occur by defining expressions using
the API instead of the notation, or as the result of inlining
optimizations.

[PEG]: https://bford.info/pub/lang/peg
