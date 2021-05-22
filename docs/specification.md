# Specification

The **pe** grammar specification extends the [PEG][] syntactic
specification with a description of the semantic effect of parsing.
Any **pe** grammar without extended features or rule actions should
parse exactly as a standard PEG grammar.

**Contents**

- [Quick Reference](#quick-reference)
- [Grammar Syntax](#grammar-syntax)
- [Expression Types and Precedence](#expression-types-and-precedence)
- [Expression Values and Behavior](#expression-values-and-behavior)
- [Parsing Preliminaries](#parsing-preliminaries)
- [Operators](#operators)


## Quick Reference

The following is a brief description of the available operators and
their behavior. More detailed information is available in the
following sections.


| [Syntax] | [Operator]    | [Type]        | Description                                               |
| -------  | ------------- | ------------- | --------------------------------------------------------- |
| `.`      | [Dot]         | [Primary]     | Match any single character                                |
| `'abc'`  | [Literal]     | [Primary]     | Match the string 'abc'                                    |
| `"abc"`  | [Literal]     | [Primary]     | Match the string 'abc'                                    |
| `[abc]`  | [Class]       | [Primary]     | Match any one character in 'abc'                          |
| `A`      | [Nonterminal] | [Primary]     | Match the expression in definition `A`                    |
| `(e)`    | [Group]       | [Primary]     | Match the subexpression `e`                               |
| `p`      | (default)     | [Quantified]  | Match primary term `p` exactly once                       |
| `p?`     | [Optional]    | [Quantified]  | Match `p` zero or one times                               |
| `p*`     | [Star]        | [Quantified]  | Match `p` zero or more times                              |
| `p+`     | [Plus]        | [Quantified]  | Match `p` one or more times                               |
| `q`      | (default)     | [Valued]      | Match quantified term `q`; consume input; pass up values  |
| `&q`     | [And]         | [Valued]      | Succeed if `q` matches; consume no input; suppress values |
| `!q`     | [Not]         | [Valued]      | Fail if `q` matches; consume no input; suppress values    |
| `~q`     | [Capture]     | [Valued]      | Match `q`; consume input; emit substring matched by `q`   |
| `name:q` | [Bind]        | [Valued]      | Match `q`; consume input; bind value to 'name'            |
| `v`      | (default)     | [Sequential]  | Match valued term `v`                                     |
| `v s`    | [Sequence]    | [Sequential]  | Match sequential term `s` only if `v` succeeded           |
| `s`      | (default)     | [Applicative] | Match sequential term `s`                                 |
| (none)   | [Rule]        | [Applicative] | Match sequential term `s`, apply the defined action       |
| `a`      | (default)     | [Prioritized] | Match applicative term `a`                                |
| `a / e`  | [Choice]      | [Prioritized] | Match prioritized term `e` only if `a` failed             |
| `A <- e` | [Grammar]     | [Definitive]  | Match prioritized term `e` for start symbol `A`           |


## Grammar Syntax
[Syntax]: #grammar-syntax

The following is a formal description of **pe**'s PEG syntax
describing itself. This PEG is based on Bryan Ford's original
[paper][PEG].


```julia
# Hierarchical syntax
Start      <- Spacing (Grammar / Expression) EndOfFile
Grammar    <- Definition+
Definition <- Identifier Operator Expression
Operator   <- LEFTARROW
Expression <- Sequence (SLASH Sequence)*
Sequence   <- Evaluated*
Evaluated  <- (prefix:Prefix)? Quantified
Prefix     <- AND / NOT / TILDE / Binding
Binding    <- Identifier COLON
Quantified <- Primary (quantifier:Quantifier)?
Quantifier <- QUESTION / STAR / PLUS
Primary    <- Name / Group / Literal / Class / DOT
Name       <- Identifier !Operator
Group      <- OPEN Expression CLOSE

# Lexical syntax
Identifier <- ~(IdentStart IdentCont*) Spacing
IdentStart <- [a-zA-Z_]
IdentCont  <- IdentStart / [0-9]

Literal    <- ~(['] ( !['] Char )* [']) Spacing
            / ~(["] ( !["] Char )* ["]) Spacing

Class      <- ~('[' ( !']' Range )* ']') Spacing
Range      <- Char '-' Char / Char
Char       <- '\\' [tnvfr"'-\[\\\]]
            / '\\' Oct Oct? Oct?
            / '\\' 'x' Hex Hex
            / '\\' 'u' Hex Hex Hex Hex
            / '\\' 'U' Hex Hex Hex Hex Hex Hex Hex Hex
            / !'\\' .
Oct        <- [0-7]
Hex        <- [0-9a-fA-F]

LEFTARROW  <- '<-' Spacing
SLASH      <- '/' Spacing
AND        <- '&' Spacing
NOT        <- '!' Spacing
TILDE      <- '~' Spacing
COLON      <- ':' Spacing
QUESTION   <- '?' Spacing
STAR       <- '*' Spacing
PLUS       <- '+' Spacing
OPEN       <- '(' Spacing
CLOSE      <- ')' Spacing
DOT        <- '.' Spacing

Spacing    <- (Space / Comment)*
Comment    <- '#' (!EndOfLine .)* EndOfLine
Space      <- ' ' / '\t' / EndOfLine
EndOfLine  <- '\r\n' / '\n' / '\r'
EndOfFile  <- !.
```


## Expression Types and Precedence


### Expression Types
[Type]: #expression-types-and-precedence

##### Primary
[Primary]: #primary

Primary expressions include terminals ([Dot], [Literal], or [Class]),
[nonterminal] symbols, and [grouped](#group) expressions. They are
the only expression type that may be quantified.

##### Quantified
[Quantified]: #quantified

Quantified expressions indicate how many times they must occur for the
expression to match. The default (unannotated) quantified expression
must occur exactly once. The [Optional], [Star], and [Plus] operators
change this number.

##### Valued
[Valued]: #valued

Valued expressions specify the semantic effects of the expression,
such as whether it consumes input, emits values, or binds values to
names. The default (unannotated) valued expression consumes the input
of its match and passes up any emitted or bound values. The [And],
[Not], [Capture], and [Bind] operators all may change some of these
effects, such as whether input is consumed or what happens with
emitted or bound values.

##### Sequential
[Sequential]: #sequential

Sequential expressions match multiple valued expressions in sequence.
Emitted and bound values are accumulated as each subexpression in the
sequence is parsed.

##### Applicative
[Applicative]: #applicative

Applicative expressions match a single sequential expression and apply
an action on its result. The default applicative expression (without
an action) passes up emitted and bound values as they are. A [Rule]
with an action transforms the emitted and bound values.

##### Prioritized
[Prioritized]: #prioritized

Prioritized expressions match multiple applicative expressions as a
prioritized choice; only the first expression to match is used. The
emitted and bound values of the first matching expression are passed
up.

##### Definitive
[Definitive]: #definitive

Definitive expressions are associated with a nonterminal symbol in a
[Grammar]. When a nonterminal symbol appears within an expression, it
is as if the expression defined by that nonterminal appeared
in-situ. That is, no special treatment is given to definitive
expressions compared to the equivalent in-situ expression.


### Operator Precedence

| [Syntax]       | [Operator] | Precedence | Expression Type |
| -------------- | ---------- | ---------- | --------------- |
| `.`            | [Dot]      | 6          | [Primary]       |
| `" "` or `' '` | [Literal]  | 6          | [Primary]       |
| `[ ]`          | [Class]    | 6          | [Primary]       |
| `Abc`          | [Name]     | 6          | [Primary]       |
| `(e)`          | [Group]    | 6          | [Primary]       |
| `e?`           | [Optional] | 5          | [Quantified]    |
| `e*`           | [Star]     | 5          | [Quantified]    |
| `e+`           | [Plus]     | 5          | [Quantified]    |
| `&e`           | [And]      | 4          | [Valued]        |
| `!e`           | [Not]      | 4          | [Valued]        |
| `~e`           | [Capture]  | 4          | [Valued]        |
| `name:e`       | [Bind]     | 4          | [Valued]        |
| `e1 e2`        | [Sequence] | 3          | [Sequential]    |
| (none)         | [Rule]     | 2          | [Applicative]   |
| `e1 / e2`      | [Choice]   | 1          | [Prioritized]   |
| `Abc <- e`     | [Grammar]  | 0          | [Definitive]    |


## Expression Values and Behavior

During parsing, **pe** accumulates and transforms values in two
channels: the *emitted-value sequence* and the *bound-value
mapping*. The [Capture] and [Rule] expressions *emit* values, i.e.,
introduce a value onto the emitted-value sequence. The [Bind]
expression *binds* a [determined] value to a name in the bound-value
mapping. The [And], [Not], [Capture], and [Rule] expressions also
*suppress* previously emitted or bound values, while [Bind] only
suppresses the previously emitted values. All other expressions *pass
up* any emitted or bound values.


### Value Determination
[determined]: #value-determination

When [Bind] associates a name with values or when getting the final
value of a parsing expression match, the following routine selects, or
*determines*, the actual value from the emitted-value sequence:

1. If there are any emitted values, the first value is returned and
   the rest are suppressed
2. Otherwise, `None` is returned

Thus, if one wants all emitted values to be returned, they must
explicitly pack them into a data structure such as a list.


### Emitted and Bound Values

An emitted value is one that becomes a positional argument for any
function applied on a [Rule], or is returned as the value of an
expression, while bound values become keyword arguments in
functions. This distinction allows **pe** to map the results of a
parse to perhaps any Python function.

The following table gives parsing expressions, the input string parsed
by the expressions, then the emitted and bound values that would
result from such a parse:

| Expression       | Input | Emitted-Value Sequence | Bound-Value Mapping |
| ---------------- | ----- | ---------------------- | ------------------- |
| `'a'`            | `a`   | `()`                   | `{}`                |
| `~'a'`           | `a`   | `('a',)`               | `{}`                |
| `~'a'*`          | `aaa` | `('aaa',)`             | `{}`                |
| `(~'a')*`        | `aaa` | `('a', 'a', 'a')`      | `{}`                |
| `'a' ~'b'`       | `ab`  | `('b',)`               | `{}`                |
| `~('a' 'b')`     | `ab`  | `('ab',)`              | `{}`                |
| `x:'a' 'b'`      | `ab`  | `()`                   | `{}`                |
| `x:'a' ~'b'`     | `ab`  | `('b',)`               | `{}`                |
| `x:(~'a') 'b'`   | `ab`  | `()`                   | `{'x': 'a'}`        |
| `x:(~'a' ~'b')`  | `ab`  | `()`                   | `{'x': 'a'}`        |
| `x:(~('a' 'b'))` | `ab`  | `()`                   | `{'x': 'ab'}`       |
| `&(x:('a'))`     | `a`   | `()`                   | `{}`                |


## Parsing Preliminaries


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

    ! " # & ' ( ) * + . / : ? [ \ ] _ ~

Special characters inside [string literals](#literal) and [character
classes](#class) are different. For both, the `\` character is used
for [escape sequences](#escape-sequences), and therefore it must be
escaped for the literal character. In addition, the following must be
escaped:

- `'` in single-quoted string literals
- `"` in double-quoted string literals
- `[` and `]` inside character classes

The other ASCII punctuation characters are currently unused but are
reserved in expressions for potential future uses:

    $ % , - ; < = > @ ` { | }


### Whitespace

Whitespace, including the space, tab, and newline characters (which
include `\n`, `\r`, and `\r\n` sequences) are only significant in
in some contexts:

* To delimit terms in a [sequence](#sequence).
* To terminate a [comment](#comments).
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
- `\"`: `"` character
- `\'`: `'` character
- `\[`: `[` character
- `\]`: `]` character
- `\\`: `\` character
- `\N`, `\NN`, `\NNN`: octal sequence of one to three octal digits; the
  maximum value is `\777`; leading zeros are permitted
- `\xNN`: sequence of exactly 2 hexidecimal digits
- `\uNNNN`: sequence of exactly 4 hexadecimal digits
- `\UNNNNNNNN`: sequence of exactly 8 hexadecimal digits

All other escape sequences are invalid.

Note that for the octal and hexadecimal escapes, each sequence
corresponds to a single character. That is, multiple UTF-8 or UTF-16
escapes are not combined into a single character.


## Operators
[Operator]: #operators

This document defines the operators available in **pe**.


### Dot
[Dot]: #dot

- Notation: `.`
- Function: [Dot](api/pe.operators.md#Dot)()
- Type: [Primary]

The Dot operator always succeeds if there is any remaining input and
fails otherwise. It consumes a single [character](#characters).


### Literal
[Literal]: #literal

- Notation: `'abc'` or `"abc"`
- Function: [Literal](api/pe.operators.md#Literal)(*string*)
- Type: [Primary]

A Literal operator (also called a *string literal* or *string*)
succeeds if the input at the current position matches the given string
exactly and fails otherwise. It consumes input equal in amount to the
length of the given string.

The `'`, `"`, and `\` characters are special inside a string and must
be [escaped](#escape-sequences) if they are used literally, however
the `'` character may be used unescaped inside a double-quoted string
(e.g, `"'"`) and the `"` character may be used unescaped inside a
single-quoted string (e.g., `'"'`).

Note that newlines do not need to be escaped but doing so can make an
expression more explicit and, thus, more clear.


### Class
[Class]: #class

- Notation: `[abc]`
- Function: [Class](api/pe.operators.md#Class)(*ranges*)
- Type: [Primary]

The Class operator (also called a *character class*) succeeds if the
next [character](#characters) of input is in a set of characters
defined by the given character ranges. It fails if the next character
is not in the set or if there is no remaining input. On success, it
consumes one character of input.

Each range is either one (possibly [escaped](#escape-sequences))
character or two (possibly escaped) characters separated by `-`. In
the former case, the range consists of the single character. In the
latter case, the range consists of the character before the `-`, the
character after the `-`, and all characters that occur between these
two in the unicode tables. The set of characters used by the class is
the union of all ranges.

It is invalid if a range separated by `-` has a first character with a
value higher than the second character.

The `[`, `]`, and `\` characters are special inside a character class
and must be escaped if they are used literally. To use the `-`
character literally, place it at one of the following locations:

- at the beginning of the character class (e.g., `[-a-z]` matches `-`
  or `a` through `z`)
- immediately after a range (`[a-z-_]` matches `a` through `z` or `-`
  or `_`, `[a-z--/]` matches `a` through `z` or `-` through `/`)
- as the second character of a range (`[*--/]` matches `*` through `-`
  or `/`)

If the `-` is meant literally in a character class, it is recommended
to be placed as the first character to avoid confusion.


### Nonterminal
[Nonterminal]: #nonterminal

- Notation: `Abc`
- Function: [Nonterminal](api/pe.operators.md#Nonterminal)(*name*)
- Type: [Primary]

A Nonterminal operator is given by an [identifier](#identifiers) in an
expression. It corresponds to a grammar [rule](#rule) of the same
name. A nonterminal operator succeeds if, at the current position in
the input, the expression of the named grammar rule succeeds at the
same position. Similarly, it fails if the grammar rule fails at the
same position.

In all cases, the behavior of the nonterminal is the same as if the
corresponding rule's expression had been written in place of the
nonterminal. Schematically, that means that `A1` and `A2` below are
equivalent for any expression `e`.

```julia
A1 <- B
B  <- e

A2 <- e
```


### Group
[Group]: #group

- Notation: `(e)`
- Function: (none)
- Type: [Primary]

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
[Optional]: #optional

- Notation: `e?`
- Function: [Optional](api/pe.operators.md#Optional)(*expression*)
- Type: [Quantified]

The Optional operator succeeds whether the given expression succeeds
or fails. If the given expression succeeds, the values and consumed
input are the same as that of the given expression. If the given
expression fails, no input is consumed and no values are passed up.

Note that the Optional operator also succeeds when there is no
remaining input.


### Star
[Star]: #star

- Notation: `e*`
- Function: [Star](api/pe.operators.md#Star)(*expression*)
- Type: [Quantified]

The Star operator succeeds if the given expression succeeds zero or
more times. Emitted values of the given expression are accumulated
while bound values get overwritten (therefore only the value bound by
the last match is passed up).

Note that the Star operator also succeeds when there is no remaining
input.


### Plus
[Plus]: #plus

- Notation: `e+`
- Function: [Plus](api/pe.operators.md#Plus)(*expression*)
- Type: [Quantified]

The Plus operator succeeds if the given expression succeeds one or
more times. Emitted values of the given expression are accumulated
while bound values get overwritten (therefore only the value bound by
the last match is passed up).


### And
[And]: #and

- Notation: `&e`
- Function: [And](api/pe.operators.md#And)(*expression*)
- Type: [Valued]

The And operator (also called *positive lookahead*) succeeds when the
given expression succeeds at the current position in the input, but no
input is consumed (even if the given expression would otherwise
consume input) and no values are passed up.


### Not
[Not]: #not

- Notation: `!e`
- Function: [Not](api/pe.operators.md#Not)(*expression*)
- Type: [Valued]

The Not operator (also called *negative lookahead*) succeeds when the
given expression fails at the current position in the input, but no
input is consumed and no values are passed up.


### Capture
[Capture]: #capture

- Notation: `~e`
- Function: [Capture](api/pe.operators.md#Capture)(*expression*)
- Type: [Valued]

The Capture operator succeeds when the given expression succeeds at
the current position in the input. It suppresses any emitted or bound
values and bindings from the given expression and then emits the
substring matched by the given expression.


### Bind
[Bind]: #bind

- Notation: `:e` or `name:e`
- Function: [Bind](api/pe.operators.md#Bind)(*expression, name*)
- Type: [Valued]

The Bind operator succeeds when the given expression succeeds at the
current position in the input. It associates the [determined] value of
the given expression with the given name in the bound-variable
mapping. Any other previously bound values are passed up, but any
values emitted by the given expression are then suppressed.


### Sequence
[Sequence]: #sequence

- Notation: `e e`
- Function: [Sequence](api/pe.operators.md#Sequence)(*expression*, ...)
- Type: [Sequential]

The Sequence operator succeeds when all of its given expressions
succeed, in turn, from the current position in the input. After an
expression succeeds, possibly consuming input, successive expressions
start matching at the new position in the input, and so on. The
Sequence operator passes up the accumulated values of its given
expressions. If any given expression fails, the entire Sequence fails
and no values are passed up and no input is consumed.

A Sequence with no given expressions is invalid. A Sequence with one
given expression is reduced to the given expression only.


### Rule
[Rule]: #rule

- Notation: (none)
- Function: [Rule](api/pe.operators.md#Rule)(*expression, action, name='\<anonymous\>'*)
- Type: [Applicative]

A Rule is often associated with a name in the grammar, but the rule
itself is just a wrapper around a given expression that defines an
action that transforms the emitted and bound values of the given
expression. The rule thus succeeds when the given expression succeeds,
and it consumes the input of the given expression. The emitted and
bound values of a rule are those returned by the action, and all
previously emitted or bound values are suppressed.

Note that, while Rules may only be defined in the PEG notation with a
name in the grammar, anonymized rules may appear inside of
expressions. This situation can occur by defining expressions using
the API instead of the notation, or as the result of inlining
optimizations. To help with debugging a grammar with inlined rules,
the name of an associated nonterminal is kept with the rule, even
though it has no other use.


### Choice
[Choice]: #choice

- Notation: `e / e`
- Function: [Choice](api/pe.operators.md#Choice)(*expression*, ...)
- Type: [Prioritized]

The Choice operator succeeds when any of its given expressions
succeeds. If a given expression fails, the next given expression is
attempted at the current position in the input. If a given expression
succeeds, the Choice operator succeeds and immediately passes up the
given expression's values and consumes its input.

A Choice with no given expressions is invalid. A Choice with one given
expression is reduced to the given expression only.


### Grammar
[Grammar]: #grammar

- Notation: `Abc <- e`
- Function: [Grammar](api/pe.operators.md#Grammar)(*definitions=None, actions=None, start='Start'*)
- Type: [Definitive]


[PEG]: https://bford.info/pub/lang/peg
