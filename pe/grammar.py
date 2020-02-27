
r"""
Self-hosted parser for pe's grammar format.

The grammar syntax, shown below, is a superset of Bryan Ford's PEG
syntax. It extends the original syntax with the following features:

* **anonymous expressions:** a full grammar is not necessary if one
  wants to match a single expression.

* **capturing groups:** used to filter and structure matches

* **extended repetition:** repetition with explicit bounds or
  interstitial expressions


The syntax is defined as follows::

  # Hierarchical syntax
  Start      <- Spacing (Expression / Grammar) EndOfFile
  Grammar    <- Definition+
  Definition <- Identifier LEFTARROW Expression
  Expression <- Sequence (SLASH Sequence)*
  Sequence   <- Prefix*
  Prefix     <- (AND / NOT)? Suffix
  Suffix     <- Primary Quantifier?
  Quantifier <- QUESTION / STAR / PLUS / Repetition
  Repetition <- LBRACE (Delimiter / Span Delimiter?) RBRACE
  Delimiter  <- COLON Expression?
  Primary    <- Identifier !LEFTARROW
              / OPEN Expression CLOSE
              / Literal
              / Class
              / DOT

  # Lexical syntax
  Identifier <- IdentStart IdentCont* Spacing
  IdentStart <- [a-zA-Z_]
  IdentCont  <- IdentStart / [0-9]

  Literal    <- ['] (!['] Char)* ['] Spacing
              / ["] (!["] Char)* ["] Spacing
  Class      <- '[' (!']' Range)* ']' Spacing
  Range      <- Char '-' Char / Char
  Char       <- '\\' [nrt'"\[\]\\]
              / '\\' [0-2] [0-7] [0-7]
              / '\\' [0-7] [0-7]?
              / !'\\' .

  Span       <- Integer? COMMA Integer? / Integer
  Integer    <- '0' / [1-9] [0-9]*

  LEFTARROW  <- '<-'  Spacing
  SLASH      <- '/' Spacing
  AND        <- '&' Spacing
  NOT        <- '!' Spacing
  QUESTION   <- '?' Spacing
  STAR       <- '*' Spacing
  PLUS       <- '+' Spacing
  OPEN       <- '(' ('?' .)? Spacing
  CLOSE      <- ')' Spacing
  DOT        <- '.' Spacing
  LBRACE     <- '{' Spacing
  RBRACE     <- '}' Spacing
  COMMA      <- ',' Spacing
  COLON      <- ':' Spacing

  Spacing    <- (Space / Comment)*
  Comment    <- '#' (!EndOfLine .)* EndOfLine
  Space      <- ' ' / '\t' / EndOfLine
  EndOfLine  <- '\r\n' / '\n' / '\r'
  EndOfFile  <- !.
"""

from pe.core import Expression
from pe.terms import (
    Dot,
    Class,
)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    Group,
    Peek,
    Not,
    Rule,
    Grammar,
)

G = Grammar()

_DOT = Dot()

# Lexical expressions

EndOfFile  = Not(_DOT)
EndOfLine  = Choice(r'\r\n', r'\r', r'\n')
Comment    = Sequence('#', Repeat(Sequence(Not(EndOfLine), _DOT)), EndOfLine)
Space      = Choice(' ', r'\t', EndOfLine)
Spacing    = Repeat(Choice(Space, Comment))

LEFTARROW  = Sequence('<-', Spacing)
SLASH      = Sequence('/', Spacing)
AND        = Sequence('&', Spacing)
NOT        = Sequence('!', Spacing)
QUESTION   = Sequence('?', Spacing)
STAR       = Sequence('*', Spacing)
PLUS       = Sequence('+', Spacing)
_GroupType = Optional(Sequence('?', _DOT))
OPEN       = Sequence('(', Group(_GroupType), Spacing)
CLOSE      = Sequence(')', Spacing)
DOT        = Sequence('.', Spacing)
LBRACE     = Sequence('{', Spacing)
RBRACE     = Sequence('}', Spacing)
COMMA      = Sequence(',', Spacing)
COLON      = Sequence(':', Spacing)

_ESC = Sequence('\\', _DOT)  # Generic escape sequence

CLASS      = Sequence(
        '[', Repeat(Class(r'^\]\\'), delimiter=Repeat(_ESC)), ']')
LITERAL    = Choice(
    Sequence("'", Repeat(Class(r"^'\\"), delimiter=Repeat(_ESC)), "'"),
    Sequence("'", Repeat(Class(r'^"\\'), delimiter=Repeat(_ESC)), '"'))

IdentStart = Class('a-zA-Z_')
IdentCont  = Choice(IdentStart, Class('0-9'))
Identifier = Sequence(
    IdentStart, Repeat(IdentCont), Spacing)

RULENAME   = Sequence(Identifier, Not(LEFTARROW))
GROUP      = Sequence(OPEN, Group(G['Expression']), CLOSE)

Integer    = Choice('0', Sequence(Class('1-9'), Repeat(Class('0-9'))))
Span       = Choice(Sequence(Optional(Integer), COMMA, Optional(Integer)),
                    Integer)

G['Dot']        = Rule(DOT, action=lambda: ('Dot', _DOT))
G['Class']      = Rule(CLASS, action=lambda s: ('Class', Class(s[1:-1])))
G['Literal']    = Rule(LITERAL, action=lambda s: ('Literal', Literal(s[1:-1])))
G['Name']       = Rule(RULENAME, action=lambda s: ('Name', s))
G['Group']      = Rule(GROUP, action=lambda xs: ('Group', *xs))
G['Term']       = Rule(Choice(G['Literal'], G['Class'], G['Dot']),
                       action=lambda t: ('Term', t))
G['Primary']    = Choice(G['RuleName'], G['Group'], G['Term'])

G['Quantifier'] = Choice(G['QUESTION'], G['STAR'], G['PLUS'], G['Repetition'])
G['Suffix']     = Sequence(G['Primary'], G['Quantifier'])
G['Prefix']     = Sequence(
    Optional(Choice(G['AND'], G['NOT'])), G['Suffix'])
G['Sequence']   = Repeat(G['Prefix'])
G['Expression'] = Repeat(G['Sequence'], delimiter=G['SLASH'])

G['Definition'] = Sequence(G['Identifier'], G['LEFTARROW'], G['Expression'])
G['Grammar']    = Rule(Repeat(G['Definition'], min=1))
G['Start']      = Sequence(
    G['Spacing'], Group(Choice(G['Expression'], G['Grammar'])), G['EndOfFile'])

# Rename the variable
PEG = G
del G
