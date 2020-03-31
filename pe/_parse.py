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

The syntax is defined as follows::

  # Hierarchical syntax
  Start      <- :Spacing (Grammar / Expression) :EndOfFile
  Grammar    <- Definition+
  Definition <- Identifier :Operator Expression
  Operator   <- Spacing LEFTARROW
  Expression <- Sequence (:SLASH Sequence)*
  Sequence   <- Evaluated*
  Evaluated  <- prefix:Prefix? Quantified
  Prefix     <- AND / NOT / TILDE / Binding / COLON
  Binding    <- Identifier ':' :Spacing
  Quantified <- Primary quantifier:Quantifier?
  Quantifier <- QUESTION / STAR / PLUS
  Primary    <- Name / Group / Literal / Class / DOT
  Name       <- Identifier :Spacing !Operator
  Group      <- :OPEN Expression :CLOSE

  # Lexical syntax
  Identifier <- IdentStart IdentCont*
  IdentStart <- [a-zA-Z_]
  IdentCont  <- IdentStart / [0-9]

  Literal    <- :['] ( !['] Char )* :['] :Spacing
              / :["] ( !["] Char )* :["] :Spacing

  Class      <- :'[' ( !']' Range )* :']' :Spacing
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
"""

from typing import Union

import pe
from pe._errors import Error
from pe._definition import Definition
from pe._grammar import Grammar
from pe.operators import (
    Dot,
    Literal,
    Class,
    Nonterminal,
    Optional,
    Star,
    Plus,
    And,
    Not,
    Raw,
    Discard,
    Bind,
    Sequence,
    Choice,
    SymbolTable,
)
from pe.packrat import PackratParser
from pe.actions import constant, first, pack, join


def _make_literal(s):
    return Literal(pe.unescape(s[1:-1]))


def _make_quantified(primary, quantifier=None):
    if not quantifier:
        return primary
    assert len(quantifier) == 1
    quantifier = quantifier[0]
    if quantifier == '?':
        return Optional(primary)
    elif quantifier == '*':
        return Star(primary)
    elif quantifier == '+':
        return Plus(primary)
    else:
        raise Error(f'invalid quantifier: {quantifier!r}')


def _make_valued(quantified, prefix=None):
    if not prefix:
        return quantified
    assert len(prefix) == 1
    prefix = prefix[0]
    if prefix == '&':
        return And(quantified)
    elif prefix == '!':
        return Not(quantified)
    elif prefix == '~':
        return Raw(quantified)
    elif prefix == ':':
        return Discard(quantified)
    elif prefix.endswith(':'):
        name = prefix[:-1]
        return Bind(quantified, name=name)
    else:
        raise Error(f'invalid prefix: {prefix!r}')


def _make_sequential(exprs):
    if len(exprs) == 1:
        return exprs[0]
    elif len(exprs) > 1:
        return Sequence(*exprs)
    else:
        raise Error(f'empty sequence: {exprs}')


def _make_prioritized(exprs):
    if len(exprs) == 1:
        return exprs[0]
    elif len(exprs) > 1:
        return Choice(*exprs)
    else:
        raise Error(f'empty choice: {exprs}')


def _make_grammar(*defs):
    if defs:
        start = defs[0][0]
    return Grammar(dict(defs), start=start)


V = SymbolTable()

# Hierarchical syntax
V.Start      = Sequence(V.Spacing, Choice(V.Grammar, V.Expression), V.EOF)
V.Grammar    = Plus(V.Definition)
V.Definition = Sequence(V.Identifier, V.Operator, V.Expression)
V.Expression = Sequence(V.Sequence,
                        Star(Sequence(Discard(V.SLASH), V.Sequence)))
V.Sequence   = Plus(V.Evaluated)
V.Evaluated  = Sequence(Bind(Optional(V.Prefix), name='prefix'), V.Quantified)
V.Prefix     = Choice(V.AND, V.NOT, V.TILDE, V.Binding)
V.Binding    = Sequence(Optional(V.Identifier), ':', V.Spacing)
V.Quantified = Sequence(V.Primary,
                        Bind(Optional(V.Quantifier), name='quantifier'))
V.Quantifier = Choice(V.QUESTION, V.STAR, V.PLUS)
V.Primary    = Choice(V.Name,
                      V.Group,
                      V.Literal,
                      V.Class,
                      V.Dot)
V.Name       = Sequence(V.Identifier, V.Spacing, Not(V.Operator))
V.Group      = Sequence(Discard(V.OPEN), V.Expression, Discard(V.CLOSE))
V.Literal    = Sequence(
    Choice(
        Raw(Sequence("'", Star(Sequence(Not("'"), V.Char)), "'")),
        Raw(Sequence('"', Star(Sequence(Not('"'), V.Char)), '"'))),
    V.Spacing)
V.Class      = Sequence(Discard('['),
                        Star(Sequence(Not(']'), V.Range)),
                        Discard(']'),
                        V.Spacing)
V.Dot        = Discard(V.DOT)

# Non-recursive patterns

V.Operator   = Sequence(V.Spacing, Discard(V.LEFTARROW))
V.Special    = Class('-tnvfr"\'[]\\\\')
V.Oct        = Class('0-7')
V.Hex        = Class('0-9a-fA-F')
V.Octal      = Sequence(V.Oct, Optional(V.Oct), Optional(V.Oct))
V.UTF8       = Sequence('x', *([V.Hex] * 2))
V.UTF16      = Sequence('u', *([V.Hex] * 4))
V.UTF32      = Sequence('U', *([V.Hex] * 8))
V.Char       = Choice(Sequence('\\',
                               Choice(V.Special,
                                      V.Octal,
                                      V.UTF8,
                                      V.UTF16,
                                      V.UTF32)),
                      Sequence(Not('\\'), Dot()))
V.Range      = Choice(Sequence(V.Char, '-', V.Char), V.Char)
V.IdentStart = Class('a-zA-Z_')
V.IdentCont  = Class('a-zA-Z_0-9')
V.Identifier = Sequence(V.IdentStart, Star(V.IdentCont))

# Tokens

V.LEFTARROW  = Sequence('<-', V.Spacing)
V.SLASH      = Sequence('/', V.Spacing)
V.AND        = Sequence('&', V.Spacing)
V.NOT        = Sequence('!', V.Spacing)
V.TILDE      = Sequence('~', V.Spacing)
V.QUESTION   = Sequence('?', V.Spacing)
V.STAR       = Sequence('*', V.Spacing)
V.PLUS       = Sequence('+', V.Spacing)
V.OPEN       = Sequence('(', V.Spacing)
V.CLOSE      = Sequence(')', V.Spacing)
V.DOT        = Sequence('.', V.Spacing)

# Whitespace and comments

V.Spacing    = Discard(Star(Choice(V.Space, V.Comment)))
V.Space      = Choice(Class(' \t'), V.EOL)
V.Comment    = Sequence('#',
                        Star(Sequence(Not(V.EOL), Dot())),
                        Optional(V.EOL))
V.EOF        = Discard(Not(Dot()))
V.EOL        = Discard(Choice('\r\n', '\n', '\r'))

PEG = Grammar(
    definitions=V,
    actions={
        'Start': first,
        'Grammar': _make_grammar,
        'Definition': pack(tuple),
        'Expression': pack(_make_prioritized),
        'Sequence': pack(_make_sequential),
        'Evaluated': _make_valued,
        'Prefix': join(str),
        'Quantified': _make_quantified,
        'Identifier': join(str),
        # 'Group': _validate,
        'Name': join(Nonterminal),
        'Literal': _make_literal,
        'Class': join(Class),
        'Dot': constant(Dot()),
    }
)

_parser = PackratParser(PEG)


def loads(source: str) -> Union[Grammar, Definition]:
    """Parse the PEG at *source* and return a grammar definition."""
    m = _parser.match(source, flags=pe.STRICT)
    if not m:
        raise Error('invalid grammar')
    return m.value()
