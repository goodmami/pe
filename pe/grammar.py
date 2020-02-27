
r"""
Self-hosted parser for pe's grammar format.

The grammar syntax, shown below, is a superset of Bryan Ford's PEG
syntax. It extends the original syntax with the following features:

* **anonymous expressions:** a full grammar is not necessary if one
  wants to match a single expression.

* **expression extraction:** subexpressions can be pulled out of a
  result in order to be discarded or later referred to by name

* **generic escapes:** any `\\` escape sequence is allowed in literals
  and character classes, and their interpretation depends on the
  action

* **result unpacking:** a `*` before a sequence or repetition will
  unpack its result list into the current context; otherwise the
  result is a list

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
  Expression <- *(Sequence *(SLASH Sequence)*)
  Sequence   <- Prefixed*
  Prefixed   <- Prefix? Quantified
  Prefix     <- AND / NOT / STAR / TILDE / Extract
  Extract    <- Name? :COLON
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
    Peek,
    Not,
    Rule,
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

# Lexical expressions

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
Class      = Seq('[', Rpt(Seq(Not(']'), Range)), ']', raw=True)
Literal    = Chc(
    Seq("'", Rpt(Seq(Not("'"), Char)), "'", raw=True),
    Seq('"', Rpt(Seq(Not('"'), Char)), '"', raw=True))

IdentStart = Cls('a-zA-Z_')
IdentCont  = Chc(IdentStart, Cls('0-9'))
Identifier = Seq(IdentStart, Rpt(IdentCont), Spacing)

Name       = Seq(Identifier, Not(LEFTARROW))
Group      = Seq(OPEN, G['Expression'], CLOSE)

Quantifier = Chc(QUESTION, STAR, PLUS)
Extract    = Seq(Opt(Name), COLON)
Prefix     = Chc(AND, NOT, STAR, TILDE, Extract)
Operator   = Chc(LEFTARROW, RAWARROW)

G['Dot']        = Rule(DOT, action=lambda: ('Dot',))
G['Class']      = Rule(Class, action=lambda s: ('Class', s[1:-1]))
G['Literal']    = Rule(Literal, action=lambda s: ('Literal', s[1:-1]))
G['Name']       = Rule(Name, action=lambda s: ('Name', s))
G['Group']      = Rule(Group, action=lambda xs: ('Group', xs))
G['Primary']    = Chc(
    G['Name'], G['Group'], G['Literal'], G['Class'], G['Dot'])

G['Quantified'] = Seq(G['Primary'], Opt(Quantifier))
G['Prefixed']   = Rule(Seq(Opt(Prefix), G['Quantified']),
                       action=_make_prefixed)
G['Sequence']   = Rule(Rpt(G['Prefixed']),
                       action=lambda xs: ('Sequence', xs))
G['Expression'] = Rule(Seq(G['Sequence'], Rpt(Seq(SLASH, G['Sequence']))),
                       action=lambda xs: ('Choice', xs))

G['Definition'] = Rule(
    Seq(Identifier, Operator, G['Expression']),
    action=lambda xs: ('Rule', *xs))
G['Grammar']    = Rule(Rpt(G['Definition'], min=1),
                       action=lambda xs: ('Grammar', xs))
G['Start']      = Seq(
    Spacing, Chc(G['Expression'], G['Grammar']), EndOfFile)

# Rename the variable
PEG = G
del G
