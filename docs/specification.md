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


| [Syntax] | [Operator]    | [Type]        | [Value]    | Description                                             |
| -------  | ------------- | ------------- | ---------- | ------------------------------------------------------- |
| `.`      | [Dot]         | [Primary]     | [Atomic]   | Match any single character                              |
| `'abc'`  | [Literal]     | [Primary]     | [Atomic]   | Match the string 'abc'                                  |
| `"abc"`  | [Literal]     | [Primary]     | [Atomic]   | Match the string 'abc'                                  |
| `[abc]`  | [Class]       | [Primary]     | [Atomic]   | Match any one character in 'abc'                        |
| `A`      | [Nonterminal] | [Primary]     | [Deferred] | Match the expression in definition `A`                  |
| `(e)`    | [Group]       | [Primary]     | [Deferred] | Match the subexpression `e`                             |
| `p`      | (default)     | [Quantified]  | [Deferred] | Match primary term `p` exactly once                     |
| `p?`     | [Optional]    | [Quantified]  | [Iterable] | Match `p` zero or one times                             |
| `p*`     | [Star]        | [Quantified]  | [Iterable] | Match `p` zero or more times                            |
| `p+`     | [Plus]        | [Quantified]  | [Iterable] | Match `p` one or more times                             |
| `q`      | (default)     | [Valued]      | [Deferred] | Match quantified term `q`; consume input; emit value    |
| `&q`     | [And]         | [Valued]      | [Empty]    | Succeed if `q` matches; consume no input; emit no value |
| `!q`     | [Not]         | [Valued]      | [Empty]    | Fail if `q` matches; consume no input; emit no value    |
| `~q`     | [Raw]         | [Valued]      | [Atomic]   | Match `q`; consume input; emit substring matched by `q` |
| `name:q` | [Bind]        | [Valued]      | [Empty]    | Match `q`; consume input; bind value to 'name'          |
| `:q`     | [Bind]        | [Valued]      | [Empty]    | Match `q`; consume input; emit no value                 |
| `v`      | (default)     | [Sequential]  | [Deferred] | Match valued term `v`                                   |
| `v s`    | [Sequence]    | [Sequential]  | [Iterable] | Match sequential term `s` only if `v` succeeded         |
| `s`      | (default)     | [Applicative] | [Deferred] | Match sequential term `s`                               |
| (none)   | [Rule]        | [Applicative] | [Atomic]   | Match sequential term `s`, apply any defined action     |
| `a`      | (default)     | [Prioritized] | [Deferred] | Match applicative term `a`                              |
| `a / e`  | [Choice]      | [Prioritized] | [Iterable] | Match prioritized term `e` only if `a` failed           |
| `A <- e` | [Grammar]     | [Definitive]  | [Deferred] | Match prioritized term `e` for start symbol `A`         |


## Grammar Syntax
[Syntax]: #grammar-syntax

The following is a formal description of **pe**'s PEG syntax
describing itself. This PEG is based on Bryan Ford's original
[paper][PEG].


```julia
# Hierarchical syntax
Start      <- :Spacing (Expression / Grammar) :EndOfFile
Grammar    <- Definition+
Definition <- Identifier :Operator Expression
Operator   <- Spacing LEFTARROW
Expression <- Sequence (SLASH Sequence)*
Sequence   <- Valued*
Valued     <- Prefix? Quantified
Prefix     <- AND / NOT / TILDE / Binding / COLON
Binding    <- Identifier COLON
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
Char       <- '\\' [tnvfr"'-\[\\\]]
            / '\\' Oct Oct? Oct?
            / '\\' 'x' Hex Hex
            / '\\' 'u' Hex Hex Hex Hex
            / '\\' 'U' Hex Hex Hex Hex Hex Hex Hex Hex
            / !'\\' .
Oct        <- [0-7]
Hex        <- [0-9a-fA-F]

LEFTARROW  <- '<-' :Spacing
SLASH      <- '/' :Spacing
AND        <- '&' :Spacing
NOT        <- '!' :Spacing
TILDE      <- '~' :Spacing
COLON      <- ':' :Spacing
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


## Expression Types and Precedence

### Expression Types
[Type]: #expression-types-and-precedence

##### Primary
[Primary]: #primary

Primary expressions include terminals ([Dot], [Literal], or [Class]),
[nonterminals](#nonterminal), and [grouped](#group) expressions.  They
are the only type that may be quantified. All terminals are
[atomic](#atomic) while nonterminals and grouped expressions have a
[deferred](#deferred) value type.

##### Quantified
[Quantified]: #quantified

Quantified expressions indicate how many times they must occur for the
expression to match. The default (unannotated) quantified expression
must occur exactly once. The [Optional], [Star], and [Plus] operators
change this number. All non-default quantified expressions are
[iterable](#iterable).

##### Valued
[Valued]: #valued

Valued expressions specify the semantic effects of the expression,
such as whether it consumes input and if it emits, binds, or discards
the expression's value. The default (unannotated) valued expression
consumes the input of its match and emits its value, unless its
quantified or primary expression consumes no input or emits no
value. The [And], [Not], [Bind], and [Discard] operators change this
behavior. All non-default valued expressions are [empty](#empty).

##### Sequential
[Sequential]: #sequential

Sequential expressions match multiple valued expressions in sequence.
The default (singular) sequential expression has a
[deferred](#deferred) value type, while all sequential expressions
with multiple subexpressions are [iterable](#iterable).

##### Applicative
[Applicative]: #applicative

Applicative expressions match a single sequential expression and apply
an action on its result. The default (with no action) applicative
expression has a [deferred](#deferred) value type while one with an
action is [atomic](#atomic).

##### Prioritized
[Prioritized]: #prioritized

Prioritized expressions match multiple applicative expressions as a
prioritized choice; only the first expression to match is used. The
default (singular) prioritized expression has a [deferred](#deferred)
value type, while all prioritized expressions with multiple
subexpressions are [iterable](#iterable).


##### Definitive
[Definitive]: #definitive

Definitive expressions are associated with a nonterminal symbol in a
[Grammar]. Definitive expressions have a [deferred](#deferred) value
type.

### Operator Precedence

| [Syntax]         | [Operator] | Precedence | Expression Type |
| ---------------- | ---------- | ---------- | --------------- |
| `.`              | [Dot]      | 6          | [Primary]       |
| `" "` or `' '`   | [Literal]  | 6          | [Primary]       |
| `[ ]`            | [Class]    | 6          | [Primary]       |
| `Abc`            | [Name]     | 6          | [Primary]       |
| `(e)`            | [Group]    | 6          | [Primary]       |
| `e?`             | [Optional] | 5          | [Quantified]    |
| `e*`             | [Star]     | 5          | [Quantified]    |
| `e+`             | [Plus]     | 5          | [Quantified]    |
| `&e`             | [And]      | 4          | [Valued]        |
| `!e`             | [Not]      | 4          | [Valued]        |
| `~e`             | [Raw]      | 4          | [Valued]        |
| `:e` or `name:e` | [Bind]     | 4          | [Valued]        |
| `e1 e2`          | [Sequence] | 3          | [Sequential]    |
| (none)           | [Rule]     | 2          | [Applicative]   |
| `e1 / e2`        | [Choice]   | 1          | [Prioritized]   |
| `Abc <- e`       | [Grammar]  | 0          | [Definitive]    |


## Expression Values and Behavior

### Value Types
[Value]: #value-types

#### Empty
[Empty]: #empty

Empty expressions emit no value.

#### Atomic
[Atomic]: #atomic

Atomic expressions always emit a single value.

#### Iterable
[Iterable]: #iterable

Iterable expressions emit any number of (zero or more) values.

Note that the *iterable* type is a generalization which defines an
expression's behavior in **pe**. For example, a [Sequence] with a
known number of terminals emits values in the same way as a [Star] or
[Plus] which a priori have an unknown number of values. An *atomic*
expression (e.g., `[ab]`) may therefore behave differently from an
*iterable* expression with a single value (e.g., `'a' / 'b'`).

#### Deferred
[Deferred]: #deferred

Expressions with a deferred value type must resolve the value types of
their nonterminals or embedded expressions in order to determine their
own value type.


### Emitted and Bound Values

#### Emitted Values
[emit]: #emitted-values

An emitted value is one that becomes a primary argument for any
function applied on a [Rule], or is returned as the value of an
expression. For instance, the following table shows expressions, their
inputs, and the value of the expression. Emitted values are "passed
up" by embedded expressions until they are acted upon (used in a
function, bound, or discarded).

| Expression   | Input | Value             |
| ------------ | ----- | ----------------- |
| `'a'`        | `a`   | `'a'`             |
| `'a'*`       | `aaa` | `['a', 'a', 'a']` |
| `'a' 'b'`    | `ab`  | `['a', 'b']`      |
| `x:'a' 'b'`  | `ab`  | `['b']`           |
| `x:'a' :'b'` | `ab`  | `[]`              |
| `x:'a'`      | `a`   | `None`            |


#### Bound Values
[bound]: #bound-values

A bound value is removed from the sequence of emitted values and
associated with (or "bound to") a name. The mapping of names to bound
values is "passed up" by embedded expressions until they are used in a
rule, after which all bound values in the current context are cleared.

| Expression    | Input | Values            | Bound Values        |
| ------------- | ----- | ----------------- | ------------------- |
| `'a'`         | `a`   | `'a'`             | `{}`                |
| `x:'a' 'b'`   | `ab`  | `['b']`           | `{'x': 'a'}`        |
| `x:'a' :'b'`  | `ab`  | `[]`              | `{'x': 'a'}`        |
| `x:('a' 'b')` | `ab`  | `None`            | `{'x': ['a', 'b']}` |
| `x:(&'a')`    | `a`   | `None`            | `{'x': None}`       |


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
- `\"`: `"` character
- `\'`: `'` character
- `\-`: `-` character
- `\[`: `[` character
- `\]`: `]` character
- `\\`: `\` character
- `\N`, `\NN`, `\NNN`: octal sequence of one to three octal digits; the
  maximum value is `\777`; leading zeros are permitted; the value
  denotes a unicode character and not a byte
- `\xNN`: UTF-8 character sequence of exactly 2 hexadecimal digits
- `\uNNNN`: UTF-16 character sequence of exactly 4 hexadecimal digits
- `\UNNNNNNNN`: UTF-32 character sequence of exactly 8 hexadecimal
  digits

All other escape sequences are invalid.

Note that for UTF-8 and UTF-16, a single code-point may require more
than one escape sequence. For all others, one escape sequence
corresponds to a single character.

## Operators
[Operator]: #operators

This document defines the operators available in **pe**.

### Dot
[Dot]: #dot

- Notation: `.`
- Function: [Dot](api/pe.grammar.md#Dot)()
- Type: [Primary]
- Value: [Atomic]

The Dot operator always succeeds if there is any remaining input and
fails otherwise. It consumes a single [character](#characters) and
emits the same character as its value.


### Literal
[Literal]: #literal

- Notation: `'abc'` or `"abc"`
- Function: [Literal](api/pe.grammar.md#Literal)(*string*)
- Type: [Primary]
- Value: [Atomic]

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
[Class]: #class

- Notation: `[abc]`
- Function: [Class](api/pe.grammar.md#Class)(*ranges*)
- Type: [Primary]
- Value: [Atomic]

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

The `[`, `]`, and `\` characters are special inside a character class
and must be escaped if they are used literally. The `-` character must
be escaped if it is meant literally in a position that would otherwise
describe a range between two characters. Valid positions for the
literal usage are as follows:

- at the beginning of the character class (e.g., `[-a-z]` matches `-`
  or `a` through `z`)
- at the end of a character class (e.g., `[a-z-]` matches `a` through
  `z` or `-`)
- immediately after a range (`[a-z-_]` matches `a` through `z` or `-`
  or `_`, `[a-z--/]` matches `a` through `z` or `-` through `/`)
- as the second character of a range (`[*--/]` matches `*` through `-`
  or `/`)

If the `-` is meant literally in a character class, it is recommended
to be placed as the first character to avoid confusion. Additionally,
it is recommended that it be escaped when describing a range from or
to the `-` character as the `--` sequence is a set-difference operator
in regular expression engines which may undergird the **pe** parser.


### Nonterminal
[Nonterminal]: #nonterminal

- Notation: `Abc`
- Function: [Nonterminal](api/pe.grammar.md#Nonterminal)(*name*)
- Type: [Primary]
- Value: [Deferred]

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
[Group]: #group

- Notation: `(e)`
- Function: (none)
- Type: [Primary]
- Value: [Deferred]

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
- Function: [Optional](api/pe.grammar.md#Optional)(*expression*)
- Type: [Quantified]
- Value: [Iterable]

The Optional operator succeeds whether the given expression succeeds
or fails. If the given expression succeeds, the emitted value and
consumed input is the same as that of the given expression. If the
given expression fails, no input is consumed and no value is emitted.

Note that the Optional operator also succeeds when there is no
remaining input.


### Star
[Star]: #star

- Notation: `e*`
- Function: [Star](api/pe.grammar.md#Star)(*expression*)
- Type: [Quantified]
- Value: [Iterable]

The Star operator succeeds if the given expression succeeds zero or
more times. The accumulated values of the given expression are
emitted.

Note that the Star operator also succeeds when there is no remaining
input.


### Plus
[Plus]: #plus

- Notation: `e+`
- Function: [Plus](api/pe.grammar.md#Plus)(*expression*)
- Type: [Quantified]
- Value: [Iterable]

The Plus operator succeeds if the given expression succeeds one or
more times. The accumulated values of the given expression are
emitted.


### And
[And]: #and

- Notation: `&e`
- Function: [And](api/pe.grammar.md#And)(*expression*)
- Type: [Valued]
- Value: [Empty]

The And operator (also called *positive lookahead*) succeeds when the
given expression succeeds at the current position in the input, but no
input is consumed (even though the given expression would otherwise
consume input) and no values are emitted.


### Not
[Not]: #not

- Notation: `!e`
- Function: [Not](api/pe.grammar.md#Not)(*expression*)
- Type: [Valued]
- Value: [Empty]

The Not operator (also called *negative lookahead*) succeeds when the
given expression fails at the current position in the input, but no
input is consumed and no values are emitted.


### Raw
[Raw]: #raw

- Notation: `~e`
- Function: [Raw](api/pe.grammar.md#Raw)(*expression*)
- Type: [Valued]
- Value: [Atomic]

The Raw operator succeeds when the given expression succeeds at the
current position in the input. It ignores any values and bindings from
the given expression and emits the substring matched by the given
expression. The substring is directly taken from the input and
includes even bound or discarded matches in the given expression.


### Bind
[Bind]: #bind

- Notation: `:e` or `name:e`
- Function: [Bind](api/pe.grammar.md#Bind)(*expression, name*)
- Type: [Valued]
- Value: [Empty]

The Bind operator succeeds when the given expression succeeds at the
current position in the input. It emits no values, but the value of
the given expression is bound to the given name. Unlike the
[And](#and) operator, matching input is consumed.

The bound value depends on the value type of the bound expression:

- Empty: `None`
- Atomic: the value emitted by the atomic expression
- Iterable: the sequence of values emitted by the iterable expression

```julia
# Expression        # Input    # Bound value of 'a'
a:.                 # abcd     'a'
a:"abc"             # abcd     'abc'
a:[abc]             # abcd     'a'
a:A                 # abcd     'abc'
a:B                 # abcd     ['a', 'b', 'c']
a:.*                # abcd     ['a', 'b', 'c', 'd']
a:("a" / A)         # abcd     ['a']
a:C                 # abcd     'abc'

# Rules
A <- "abc"
B <- "a" "b" "c"
C <- A
```

### Discard
[Discard]: #discard

- Notation: `:e`
- Function: [Discard](api/pe.grammar.md#Discard)(*expression*)
- Type: [Valued]
- Value: [Empty]

The Discard operator succeeds when the given expression succeeds at
the current position in the input, but no values are emitted. Unlike
the [And](#and) operator, matching input is consumed.


### Sequence
[Sequence]: #sequence

- Notation: `e e`
- Function: [Sequence](api/pe.grammar.md#Sequence)(*expression*, ...)
- Type: [Sequential]
- Value: [Iterable]

The Sequence operator succeeds when all of its given expressions
succeed, in turn, from the current position in the input. After an
expression succeeds, possibly consuming input, successive expressions
start matching at the new position in the input, and so on. The
Sequence operator emits the accumulated values of its given
expressions. If any given expression fails, the entire Sequence fails
and no values are emitted and no input is consumed.

A Sequence with no given expressions is invalid. A Sequence with one
given expression is reduced to the given expression only.


### Rule
[Rule]: #rule

- Notation: (none)
- Function: [Rule](api/pe.grammar.md#Rule)(*expression, action=None*)
- Type: [Applicative]
- Value: [Atomic]

A Rule is often associated with a name in the grammar, but the rule
itself is just a wrapper around a given expression that provides some
additional behavior. The rule thus succeeds when the given expression
succeeds, emitting the given expressions value and consuming its
input. If an action is defined, the value type of the rule is *atomic*
and it emits the result of applying the action with any emitted or
bound values. If no action is defined, the value type of the Rule is
the resolved value type of the given expression. After the rule
completes, any bound values are cleared, regardless of whether an
action was defined.

Note that, while Rules may only be defined in the PEG notation with a
name in the grammar, anonymized rules may appear inside of
expressions. This situation can occur by defining expressions using
the API instead of the notation, or as the result of inlining
optimizations.


### Choice
[Choice]: #choice

- Notation: `e / e`
- Function: [Choice](api/pe.grammar.md#Choice)(*expression*, ...)
- Type: [Prioritized]
- Value: [Iterable]

The Choice operator succeeds when any of its given expressions
succeeds. If a given expression fails, the next given expression is
attempted at the current position in the input. If a given expression
succeeds, the Choice operator succeeds and immediately emits the given
expression's value and consumes its input.

A Choice with no given expressions is invalid. A Choice with one given
expression is reduced to the given expression only.


### Grammar
[Grammar]: #grammar

- Notation: `Abc <- e`
- Function: [Grammar](api/pe.grammar.md#Grammar)(*definitions=None, actions=None, start='Start'*)
- Type: [Definitive]
- Value: [Deferred]


[PEG]: https://bford.info/pub/lang/peg
