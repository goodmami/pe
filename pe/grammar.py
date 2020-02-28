
r"""
Self-hosted parser for pe's grammar format.

The grammar syntax, shown below, is a superset of Bryan Ford's PEG
syntax. It extends the original syntax with the following features:

* **anonymous expressions:** a full grammar is not necessary if one
  wants to match a single expression.

* **expression binding:** subexpressions can be extracted from the
  result and optionally bound to a name for later reference

* **generic escapes:** any `\\` escape sequence is allowed in literals
  and character classes, and their interpretation depends on the
  action

* **raw result:** a `~` before an expression makes its result in the
  current context only the full matched string and not any
  intermediate results; this is also allowed as a special rule
  operator `<~` which returns the raw result of the entire rule


The syntax is defined as follows::

  # Hierarchical syntax
  Start      <- :Spacing (Expression / Grammar) :EndOfFile
  Grammar    <- Definition+
  Definition <- Identifier Operator Expression
  Operator   <- LEFTARROW / RAWARROW
  Expression <- Sequence (SLASH Sequence)*
  Sequence   <- Prefixed*
  Prefixed   <- Prefix? Quantified
  Prefix     <- AND / NOT / STAR / TILDE / Binding
  Binding    <- Name? :COLON
  Quantified <- Primary Quantifier?
  Quantifier <- QUESTION / STAR / PLUS
  Primary    <- Name / Group / Literal / Class / DOT
  Name       <- Identifier !LEFTARROW
  Group      <- :OPEN Expression :CLOSE

  # Lexical syntax
  Identifier <- IdentStart IdentCont* :Spacing
  IdentStart <- [a-zA-Z_]
  IdentCont  <- IdentStart / [0-9]

  Literal    <- :['] ~( !['] Char )* :['] :Spacing
              / :["] ~( !["] Char )* :["] :Spacing

  Class      <- :'[' ~( !']' Range )* :']' :Spacing
  Range      <- Char '-' Char / Char
  Char       <- '\\' . / .

  LEFTARROW  <- '<-' Spacing
  RAWARROW   <- '<~' Spacing
  SLASH      <- '/' Spacing
  AND        <- '&' Spacing
  NOT        <- '!' Spacing
  TILDE      <- '~' Spacing
  QUESTION   <- '?' Spacing
  STAR       <- '*' Spacing
  PLUS       <- '+' Spacing
  OPEN       <- '(' Spacing
  CLOSE      <- ')' Spacing
  DOT        <- '.' Spacing
  COLON      <- ':' Spacing

  Spacing    <- (?: Space / Comment)*
  Comment    <- '#' (?: !EndOfLine .)* EndOfLine
  Space      <- ' ' / '\t' / EndOfLine
  EndOfLine  <- '\r\n' / '\n' / '\r'
  EndOfFile  <- !.
"""

from pe.core import Expression
from pe.terms import (
    Dot,
    Class as Cls,
)
from pe.expressions import (
    Sequence as Seq,
    Choice as Chc,
    Repeat as Rpt,
    Optional as Opt,
    And,
    Not,
    Grammar,
)


def _make_prefixed(*args, **kwargs):
    prefix, suffix = args
    primary, quantifier = suffix


G = Grammar()

_DOT = Dot()

# Whitespace and comments

EndOfFile  = Not(_DOT)
EndOfLine  = Chc(r'\r\n', r'\n', r'\r')
Comment    = Seq('#', Rpt(Seq(Not(EndOfLine), _DOT)), EndOfLine)
Space      = Chc(' ', r'\t', EndOfLine)
Spacing    = Rpt(Chc(Space, Comment))

# Lexical syntax

LEFTARROW  = Seq('<-', Spacing)
RAWARROW   = Seq('<~', Spacing)
SLASH      = Seq('/', Spacing)
AND        = Seq('&', Spacing)
NOT        = Seq('!', Spacing)
TILDE      = Seq('~', Spacing)
QUESTION   = Seq('?', Spacing)
STAR       = Seq('*', Spacing)
PLUS       = Seq('+', Spacing)
OPEN       = Seq('(', Spacing)
CLOSE      = Seq(')', Spacing)
DOT        = Seq('.', Spacing)
COLON      = Seq(':', Spacing)

Char       = Chc(Seq('\\', _DOT), _DOT)
Range      = Chc(Seq(Char, '-', Char), Char)
Class      = Seq('[', Rpt(Seq(Not(']'), Range)), ']')
Literal    = Chc(
    Seq("'", Rpt(Seq(Not("'"), Char)), "'"),
    Seq('"', Rpt(Seq(Not('"'), Char)), '"'))

IdentStart = Cls('a-zA-Z_')
IdentCont  = Chc(IdentStart, Cls('0-9'))
Identifier = Seq(IdentStart, Rpt(IdentCont), Spacing)

Operator   = Chc(LEFTARROW, RAWARROW)
Name       = Seq(Identifier, Not(Operator))
Quantifier = Chc(QUESTION, STAR, PLUS)
Binding    = Seq(Opt(Name), COLON)
Prefix     = Chc(AND, NOT, STAR, TILDE, Binding)

G['Dot']        = DOT
G['Class']      = Class
G['Literal']    = Literal
G['Name']       = Name

# Hierarchical syntax

G['Group']      = Seq(OPEN, G['Expression'], CLOSE)
G['Primary']    = Chc(G['Name'], G['Group'], G['Literal'], G['Class'], G['Dot'])
G['Quantified'] = Seq(G['Primary'], Opt(Quantifier))
G['Prefixed']   = Seq(Opt(Prefix), G['Quantified'])
G['Sequence']   = Rpt(G['Prefixed'])
G['Expression'] = Seq(G['Sequence'], Rpt(Seq(SLASH, G['Sequence'])))
G['Definition'] = Seq(Identifier, Operator, G['Expression'])
G['Grammar']    = Rpt(G['Definition'], min=1)
G['Start']      = Seq(Spacing, Chc(G['Expression'], G['Grammar']), EndOfFile)

# Semantic actions

G.actions.update({
    'DOT': lambda: ('Dot',),
    'Class': lambda s: ('Class', s[1:-1]),
    'Literal': lambda s: ('Literal', s[1:-1]),
    'Name': lambda s: ('Name', s),
    'Group': lambda xs: ('Group', xs),
    'Prefixed': _make_prefixed,
    'Sequence': lambda xs: ('Sequence', xs),
    'Expression': lambda xs: ('Choice', xs),
    'Definition': lambda xs: ('Rule', *xs),
    'Grammar': lambda xs: ('Grammar', xs),
})

# Rename the variable
PEG = G
del G
