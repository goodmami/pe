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
  Start      <- :Spacing (Expression / Grammar) :EndOfFile
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
from pe._core import Error
from pe.operators import (
    Definition,
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
    Grammar,
)
from pe.packrat import PackratParser
from pe.actions import constant, first, pack, join


def _make_literal(*xs):
    s = ''.join(xs)
    return Literal(pe.unescape(s))


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


# Lexical productions do not need to go in the grammar

# Whitespace and comments
_EOF        = Discard(Not(Dot()))
_EOL        = Discard(Choice('\r\n', '\n', '\r'))
_Comment    = Sequence('#',
                       Star(Sequence(Not(_EOL), Dot())),
                       Optional(_EOL))
_Space      = Choice(Class(' \t'), _EOL)
_Spacing    = Discard(Star(Choice(_Space, _Comment)))

# Tokens
_LEFTARROW  = Sequence('<-', _Spacing)
_SLASH      = Sequence('/', _Spacing)
_AND        = Sequence('&', _Spacing)
_NOT        = Sequence('!', _Spacing)
_TILDE      = Sequence('~', _Spacing)
_QUESTION   = Sequence('?', _Spacing)
_STAR       = Sequence('*', _Spacing)
_PLUS       = Sequence('+', _Spacing)
_OPEN       = Sequence('(', _Spacing)
_CLOSE      = Sequence(')', _Spacing)
_DOT        = Sequence('.', _Spacing)

# Non-recursive patterns
_Operator   = Sequence(_Spacing, Discard(_LEFTARROW))
_Special    = Class('-tnvfr"\'[]\\\\')
_Oct        = Class('0-7')
_Hex        = Class('0-9a-fA-F')
_Octal      = Sequence(_Oct, Optional(_Oct), Optional(_Oct))
_UTF8       = Sequence('x', _Hex, _Hex)
_UTF16      = Sequence('u', _Hex, _Hex, _Hex, _Hex)
_UTF32      = Sequence('U', _Hex, _Hex, _Hex, _Hex, _Hex, _Hex, _Hex, _Hex)
_Char       = Choice(Sequence('\\', Choice(_Special,
                                           _Octal,
                                           _UTF8,
                                           _UTF16,
                                           _UTF32)),
                     Sequence(Not('\\'), Dot()))
_Range      = Choice(Sequence(_Char, '-', _Char), _Char)
_Class      = Sequence(
    Discard('['),
    Star(Sequence(Not(']'), _Range)),
    Discard(']'),
    _Spacing)
_Literal    = Sequence(
    Choice(
        Sequence(Discard("'"), Star(Sequence(Not("'"), _Char)), Discard("'")),
        Sequence(Discard('"'), Star(Sequence(Not('"'), _Char)), Discard('"'))),
    _Spacing)
_IdentStart = Class('a-zA-Z_')
_IdentCont  = Class('a-zA-Z_0-9')
_Identifier = Sequence(_IdentStart, Star(_IdentCont))
_Name       = Sequence(_Identifier, _Spacing, Not(_Operator))
_Quantifier = Choice(_QUESTION, _STAR, _PLUS)
_Binding    = Sequence(Optional(_Identifier), ':', _Spacing)
_Prefix     = Choice(_AND, _NOT, _TILDE, _Binding)

PEG = Grammar(
    definitions={
        # Hierarchical syntax
        'Start':      Sequence(_Spacing,
                               Choice(Nonterminal('Grammar'),
                                      Nonterminal('Expression')),
                               _EOF),
        'Grammar':    Plus(Nonterminal('Definition')),
        'Definition': Sequence(Nonterminal('Identifier'),
                               _Spacing,
                               _Operator,
                               Nonterminal('Expression')),
        'Expression': Sequence(Nonterminal('Sequence'),
                               Star(Sequence(Discard(_SLASH),
                                             Nonterminal('Sequence')))),
        'Sequence':   Plus(Nonterminal('Evaluated')),
        'Evaluated':  Sequence(Bind(Optional(Nonterminal('Prefix')),
                                    name='prefix'),
                               Nonterminal('Quantified')),
        'Quantified': Sequence(Nonterminal('Primary'),
                               Bind(Optional(_Quantifier), name='quantifier')),
        'Primary':    Choice(Nonterminal('Name'),
                             Nonterminal('Group'),
                             Nonterminal('Literal'),
                             Nonterminal('Class'),
                             Nonterminal('Dot')),
        'Identifier': _Identifier,
        'Name':       _Name,
        'Group':      Sequence(Discard(_OPEN),
                               Nonterminal('Expression'),
                               Discard(_CLOSE)),
        'Literal':    _Literal,
        'Class':      _Class,
        'Prefix':     _Prefix,
        'Dot':        Discard(_DOT),
    },
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
