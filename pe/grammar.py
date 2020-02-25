
r"""
Self-hosted parser for pe's grammar format.

The grammar syntax is a superset of Bryan Ford's PEG syntax, which
is shown below::

  # Hierarchical syntax
  Grammar    <- Spacing Definition+ EndOfFile
  Definition <- Identifier LEFTARROW Expression
  Expression <- Sequence (SLASH Sequence)*
  Sequence   <- Prefix*
  Prefix     <- (AND / NOT)? Suffix
  Suffix     <- Primary (QUESTION / STAR / PLUS)?
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

  LEFTARROW  <- '<-'  Spacing
  SLASH      <- '/' Spacing
  AND        <- '&' Spacing
  NOT        <- '!' Spacing
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

Changes to the syntax are as follows::

  # Expanded quantification
  Suffix     <- Primary Quantifier?
  Quantifier <- QUESTION / STAR / PLUS / Repetition
  Repetition <- LBRACE Span? Delimiter Escape? RBRACE
              / LBRACE Span RBRACE
  Span       <- Integer? COMMA Integer? / Integer
  Integer    <- '0' / [1-9] [0-9]*
  Delimiter  <- COLON Expression?
  Escape     <- COLON Expression?

  LBRACE     <- '{' Spacing
  RBRACE     <- '}' Spacing
  COMMA      <- ',' Spacing
  COLON      <- ':' Spacing

  # Optional group modifier
  OPEN       <- '(' ('?' .)? Spacing
"""

from pe.core import Expression
from pe import (
    Dot,
    Class,
    Sequence,
    Choice,
    Repeat,
    Optional,
    Group,
    Ahead,
    NotAhead,
    Rule,
    Grammar,
)

G = Grammar()

_DOT = Dot()
G['EndOfFile']  = NotAhead(Dot())
G['EndOfLine']  = Choice(r'\r\n', r'\r', r'\n')
_RestOfLine = Repeat(Sequence(NotAhead(G['EndOfLine']), _DOT))
G['Comment']    = Sequence('#', _RestOfLine, G['EndOfLine'])
G['Space']      = Choice(' ', r'\t', G['EndOfLine'])
G['Spacing']    = Repeat(Choice(G['Space'], G['Comment']))

G['LEFTARROW']  = Sequence('<-', G['Spacing'])
G['SLASH']      = Sequence('/', G['Spacing'])
G['AND']        = Sequence('&', G['Spacing'])
G['NOT']        = Sequence('!', G['Spacing'])
G['QUESTION']   = Sequence('?', G['Spacing'])
G['STAR']       = Sequence('*', G['Spacing'])
G['PLUS']       = Sequence('+', G['Spacing'])
_GroupType = Optional(Sequence('?', _DOT))
G['OPEN']       = Sequence('(', Group(_GroupType), G['Spacing'])
G['CLOSE']      = Sequence(')', G['Spacing'])
G['DOT']        = Sequence('.', G['Spacing'])

_ESC = Sequence('\\', _DOT)

G['Class']      = Rule(
    Sequence('[', Repeat(Class(r'^\]\\'), escape=_ESC), ']'),
    action=lambda s: Class(s[1:-1]))

G['Literal']    = Rule(
    Choice(Sequence("'", Repeat(Class(r"^'\\"), escape=_ESC), "'"),
           Sequence("'", Repeat(Class(r'^"\\'), escape=_ESC), '"')),
           action=lambda s: Literal(s[1:-1]))

G['IdentStart'] = Class('a-zA-Z_')
G['IdentCont']  = Choice(G['IdentStart'], Class('0-9'))
G['Identifier'] = Sequence(
    G['IdentStart'], Repeat(G['IdentCont']), G['Spacing'])

G['RuleName']   = Rule(
    Sequence(G['Identifier'], NotAhead(G['LEFTARROW'])),
    action=lambda s: ('Name', s))
G['Group']      = Rule(
    Sequence(G['OPEN'], Group(G['Expression']), G['CLOSE']),
    action=lambda xs: ('Group', *xs))
G['Term']       = Rule(Choice(G['Literal'], G['Class']),
                       action=lambda t: ('Term', t))
G['Primary']    = Choice(G['RuleName'], G['Group'], G['Term'])

G['Quantifier'] = Choice(G['QUESTION'], G['STAR'], G['PLUS'], G['))
G['Suffix']     = Sequence(G['Primary'], G['Quantifier'])
G['Prefix']     = Sequence(
    Optional(Choice(G['AND'], G['NOT'])), G['Suffix'])
G['Sequence']   = Repeat(G['Prefix'])
G['Expression'] = Repeat(G['Sequence'], delimiter=G['SLASH'])

G['Definition'] = Sequence(G['Identifier'], G['LEFTARROW'], G['Expression'])
G['Grammar']    = Sequence(
    G['Spacing'], Repeat(G['Definition'], min=1), G['EndOfFile'])


def compile(source) -> Expression:
    pass
