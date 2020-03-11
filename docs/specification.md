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

* *Note*: Evaluation of an expression depends on the value type:
  - Niladic -- return `None`
  - Monadic -- return the value itself
  - Variadic -- return the values as a list

## Grammar Syntax

The following is a formal description of **pe**'s PEG syntax describing
itself. This PEG is based on Bryan Ford's original
[paper][PEG].


``` sourceCode ruby
# Hierarchical syntax
Start      <- :Spacing (Expression / Grammar) :EndOfFile
Grammar    <- Definition+
Definition <- Identifier :Operator Expression
Operator   <- Spacing LEFTARROW
Expression <- Sequence (SLASH Sequence)*
Sequence   <- Evaluated*
Evaluated  <- prefix:Prefix? Quantified
Prefix     <- AND / NOT / Binding
Binding    <- Identifier? ':' :Spacing
Quantified <- Primary quantifier:Quantifier?
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
COLON      <- ':' :Spacing

Spacing    <- (Space / Comment)*
Comment    <- '#' (!EndOfLine .)* EndOfLine
Space      <- ' ' / '\t' / EndOfLine
EndOfLine  <- '\r\n' / '\n' / '\r'
EndOfFile  <- !.
```

## Operator Precedence

| Operator  | Name     | Precedence | Expression Type |
| --------- | -------- | ---------- | --------------- |
| `.`       | Dot      | 5          | Primary         |
| `" "`     | Literal  | 5          | Primary         |
| `[ ]`     | Class    | 5          | Primary         |
| `Abc`     | Name     | 5          | Primary         |
| `(e)`     | Group    | 5          | Primary         |
| `e?`      | Optional | 4          | Quantified      |
| `e*`      | Star     | 4          | Quantified      |
| `e+`      | Plus     | 4          | Quantified      |
| `&e`      | And      | 3          | Evaluated       |
| `!e`      | Not      | 3          | Evaluated       |
| `:e`      | Bind     | 3          | Evaluated       |
| `e1 e2`   | Sequence | 2          | Sequence        |
| `e1 / e2` | Choice   | 1          | Expression      |

## Semantic Values

The value of each expression is a list. For

## Expressions

This document defines the expressions available to **pe**.

### Dot

  - form  
    `.`

  - expression-type  
    primary

  - value-type  
    atomic

The Dot operator always succeeds if there is any remaining input and
fails otherwise. It consumes a single character.

### Literal

`"abc"`

### Character Class

`[abc]`

### Nonterminal Symbol

`A`

### Group

`(e)`

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

`e?`

### Star

`e*`

### Plus

`e+`

### Bind

`n:e`

`:e`

  - If the bound expression is repeated (an optional, star, or plus), a
    sequence, or a choice, or indirectly one of these through some chain
    of nonterminals to rules where no rule specifies an action, the
    associated value is the values list;
  - Otherwise, if the values list is empty, the associated value is
    `None`;
  - Otherwise, the associated value is the last item on the values list

<!-- end list -->

``` sourceCode 
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

`e e`

### Ordered Choice

`e / e`

## Value Transformations

``` sourceCode 
# Grammar                        Input  ->  Value
# -------------------------------------------------------
Start <- [0-9]                   '3'    ->  '3'
# -------------------------------------------------------
Start <- [0-9]          -> int   '3'    ->  0
# -------------------------------------------------------
Start <- ([0-9])                 '3'    ->  '3'
# -------------------------------------------------------
Start <- ([0-9])        -> int   '3'    ->  3
# -------------------------------------------------------
Start <- (([0-9]))      -> int   '3'    ->  *error*
# -------------------------------------------------------
Start <- Digit                   '3'    ->  '3'
Digit <- [0-9]
# -------------------------------------------------------
Start <- Digit                   '3'    ->  0
Digit <- [0-9]          -> int
# -------------------------------------------------------
Start <- Digit                   '3'    ->  '3'
Digit <- ([0-9])
# -------------------------------------------------------
Start <- (Digit)                 '3'    ->  '3'
Digit <- [0-9]
# -------------------------------------------------------
Start <- (Digit)                 '3'    ->  0
Digit <- [0-9]          -> int
# -------------------------------------------------------
Start <- Digit                   '3'    ->  3
Digit <- ([0-9])        -> int
```

``` sourceCode 
# Grammar                        Input  ->  Value
Start <- "-" [0-9]               '-3'   ->  '-3'
# -------------------------------------------------------
Start <- "-" [0-9]      -> int   '-3'  ->  -3
# -------------------------------------------------------
Start <- "-" ([0-9])             '-3'  ->  ['3']
# -------------------------------------------------------
Start <- "-" ([0-9])    -> int   '-3'  ->  *error*
# -------------------------------------------------------
Start <- "-" Digit               '-3'  ->  '-3'
Digit <- [0-9]
# -------------------------------------------------------
Start <- "-" Digit               '-3'  ->  ['-', 3]
Digit <- [0-9]          -> int
# -------------------------------------------------------
Start <- "-" Digit               '-3'  ->  ['-', ['3']]
Digit <- ([0-9])
# -------------------------------------------------------
Start <- "-" (Digit)             '-3'  ->  ['3']
Digit <- [0-9]
# -------------------------------------------------------
Start <- ("-") (Digit)           '-3'  ->  ['-', ['3']]
Digit <- ([0-9])
# -------------------------------------------------------
Start <- ("-") Digit             '-3'  ->  ['-']
Digit <- ([0-9])
```

[PEG]: https://bford.info/pub/lang/peg
