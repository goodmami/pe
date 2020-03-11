# Specification

The **pe** grammar specification extends the [PEG][] syntactic
specification with a description of the semantic effect of parsing.
Any **pe** grammar without extended features or rule actions should
parse exactly as a standard PEG grammar.

## Quick Reference

```ruby
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

- Niladic: No value
- Monadic: A single value
- Variadic: More than one value
- Deferred: Value type depends on resolved expression


## Grammar Syntax

The following is a formal description of **pe**'s PEG syntax describing
itself. This PEG is based on Bryan Ford's original
[paper][PEG].


```ruby
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


## Semantic Values

The value of each expression is a list. For

## Expressions

This document defines the expressions available to **pe**.

### Dot

<table>
<tr><td>**expression-form**</td><td>`.`</td></tr>
<tr><td>**API function**   </td><td>Dot()</td></tr>
<tr><td>**expression-type**</td><td>primary</td></tr>
<tr><td>**value-type**     </td><td>monadic</td></tr>
</table>

The Dot operator always succeeds if there is any remaining input and
fails otherwise. It consumes a single character.


### Literal

<table>
<tr><td>**expression-form**</td><td>`'abc'` or `"abc"`</td></tr>
<tr><td>**API function**   </td><td>Literal(*string*)</td></tr>
<tr><td>**expression-type**</td><td>primary</td></tr>
<tr><td>**value-type**     </td><td>monadic</td></tr>
</table>


### Character Class

<table>
<tr><td>**expression-form**</td><td>`[abc]`</td></tr>
<tr><td>**API function**   </td><td>Class(*ranges*)</td></tr>
<tr><td>**expression-type**</td><td>primary</td></tr>
<tr><td>**value-type**     </td><td>monadic</td></tr>
</table>


### Nonterminal Symbol

<table>
<tr><td>**expression-form**</td><td>`Abc`</td></tr>
<tr><td>**API function**   </td><td>Nonterminal(*name*)</td></tr>
<tr><td>**expression-type**</td><td>primary</td></tr>
<tr><td>**value-type**     </td><td>deferred</td></tr>
</table>


### Group

<table>
<tr><td>**expression-form**</td><td>`(e)`</td></tr>
<tr><td>**API function**   </td><td>none</td></tr>
<tr><td>**expression-type**</td><td>primary</td></tr>
<tr><td>**value-type**     </td><td>deferred</td></tr>
</table>

Groups do not actually refer to a construct in **pe**, but they are used
to aid in the parsing of a grammar. This is helpful when one wants to
apply a lower-precedence operator with a higher-precedence one, such as
a sequence of choices:

    [0-9] ' and ' / ' or ' [0-9]    # parses "1 and" or "or 2" but not "1 and 2" or "1 or 2"

    [0-9] (' and ' / ' or ') [0-9]  # parses "1 and 2", "1 or 2", etc.

Or repeated subexpressions:

    [0-9] (' and ' [0-9])*  # parses "1", "1 and 2", "3 and 5 and 8", etc.

The three expressions above would translate to the following:

    Choice(Sequence(Class('0-9'), Literal(' and ')), Sequence(Literal(' or '), Class('0-9')))

    Sequence(Class('0-9'), Choice(Literal(' and '), Literal(' or ')), Class('0-9'))

    Sequence(Class('0-9'), Star(Sequence(Literal(' and '), Class('0-9'))))

### Optional

<table>
<tr><td>**expression-form**</td><td>`e?`</td></tr>
<tr><td>**API function**   </td><td>Optional(*expression*)</td></tr>
<tr><td>**expression-type**</td><td>quantified</td></tr>
<tr><td>**value-type**     </td><td>variadic</td></tr>
</table>


### Star

<table>
<tr><td>**expression-form**</td><td>`e*`</td></tr>
<tr><td>**API function**   </td><td>Star(*expression*)</td></tr>
<tr><td>**expression-type**</td><td>quantified</td></tr>
<tr><td>**value-type**     </td><td>variadic</td></tr>
</table>


### Plus

<table>
<tr><td>**expression-form**</td><td>`e+`</td></tr>
<tr><td>**API function**   </td><td>Plus(*expression*)</td></tr>
<tr><td>**expression-type**</td><td>quantified</td></tr>
<tr><td>**value-type**     </td><td>variadic</td></tr>
</table>


### And

<table>
<tr><td>**expression-form**</td><td>`&e`</td></tr>
<tr><td>**API function**   </td><td>And(*expression*)</td></tr>
<tr><td>**expression-type**</td><td>evaluated</td></tr>
<tr><td>**value-type**     </td><td>niladic</td></tr>
</table>


### Not

<table>
<tr><td>**expression-form**</td><td>`!e`</td></tr>
<tr><td>**API function**   </td><td>Not(*expression*)</td></tr>
<tr><td>**expression-type**</td><td>evaluated</td></tr>
<tr><td>**value-type**     </td><td>niladic</td></tr>
</table>


### Bind

<table>
<tr><td>**expression-form**</td><td>`:e` or `name:e`</td></tr>
<tr><td>**API function**   </td><td>Bind(*expression*, *name*=None)</td></tr>
<tr><td>**expression-type**</td><td>evaluated</td></tr>
<tr><td>**value-type**     </td><td>niladic</td></tr>
</table>

The bound value depends on the value type of the bound expression:

- Niladic: `None`
- Monadic: the value emitted by the monadic expression
- Variadic: the sequence of values emitted by the variadic expression

```ruby
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

<table>
<tr><td>**expression-form**</td><td>`e e`</td></tr>
<tr><td>**API function**   </td><td>Sequence(*expression*, ...)</td></tr>
<tr><td>**expression-type**</td><td>sequence</td></tr>
<tr><td>**value-type**     </td><td>variadic</td></tr>
</table>


### Ordered Choice

<table>
<tr><td>**expression-form**</td><td>`e / e`</td></tr>
<tr><td>**API function**   </td><td>Choice(*expression*, ...)</td></tr>
<tr><td>**expression-type**</td><td>expression</td></tr>
<tr><td>**value-type**     </td><td>variadic</td></tr>
</table>


### Rule

<table>
<tr><td>**expression-form**</td><td>`Abc <- e`</td></tr>
<tr><td>**API function**   </td><td>Choice(*expression*, ...)</td></tr>
<tr><td>**expression-type**</td><td>expression</td></tr>
<tr><td>**value-type**     </td><td>variadic</td></tr>
</table>



[PEG]: https://bford.info/pub/lang/peg
