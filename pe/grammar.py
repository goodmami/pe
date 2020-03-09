
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
  Operator   <- LEFTARROW
  Expression <- =(Sequence (:SLASH Sequence)*)
  Sequence   <- =Evaluated*
  Evaluated  <- prefix:Prefix? Quantified
  Prefix     <- AND / NOT / TILDE / Binding / EQUAL
  Binding    <- ~(Name? ':') :Spacing
  Quantified <- Primary quantifier:Quantifier?
  Quantifier <- QUESTION / STAR / PLUS
  Primary    <- Name / Group / Literal / Class / DOT
  Name       <- Identifier !Operator
  Group      <- :OPEN Expression :CLOSE

  # Lexical syntax
  Identifier <- ~(IdentStart IdentCont*) :Spacing
  IdentStart <- [a-zA-Z_]
  IdentCont  <- IdentStart / [0-9]

  Literal    <- :['] ~( !['] Char )* :['] :Spacing
              / :["] ~( !["] Char )* :["] :Spacing

  Class      <- :'[' ~( !']' Range )* :']' :Spacing
  Range      <- Char '-' Char / Char
  Char       <- '\\' . / .

  LEFTARROW  <- '<-' Spacing
  SLASH      <- '/' Spacing
  AND        <- '&' Spacing
  NOT        <- '!' Spacing
  TILDE      <- '~' Spacing
  EQUAL      <- '=' Spacing
  QUESTION   <- '?' Spacing
  STAR       <- '*' Spacing
  PLUS       <- '+' Spacing
  OPEN       <- '(' Spacing
  CLOSE      <- ')' Spacing
  DOT        <- '.' Spacing

  Spacing    <- (?: Space / Comment)*
  Comment    <- '#' (?: !EndOfLine .)* EndOfLine
  Space      <- ' ' / '\t' / EndOfLine
  EndOfLine  <- '\r\n' / '\n' / '\r'
  EndOfFile  <- !.
"""

from typing import Union, Pattern
from operator import itemgetter

from pe.constants import Operator, Flag
from pe.core import Error, Expression, Definition, Grammar
from pe.packrat import PackratParser


_Defn = Union[str, Definition]


def _validate(arg: _Defn):
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Definition):
        raise ValueError(f'not a valid definition: {arg!r}')
    elif not isinstance(arg.op, Operator):
        raise ValueError(f'not a valid operator: {arg.op!r}')
    else:
        return arg


def Dot():
    return Definition(Operator.DOT, ())


def Literal(string: str):
    return Definition(Operator.LIT, (string,))


def Class(chars: str):
    return Definition(Operator.CLS, (chars,))


def Regex(pattern: Union[str, Pattern], flags: int = 0):
    return Definition(Operator.RGX, (pattern, flags))


def Sequence(*expressions: _Defn):
    return Definition(Operator.SEQ, (list(map(_validate, expressions)),))


def Choice(*expressions: _Defn):
    return Definition(Operator.CHC, (list(map(_validate, expressions)),))


def Repeat(expression: _Defn, min: int = 0, max: int = -1):
    return Definition(Operator.RPT, (_validate(expression), min, max))


def Optional(expression: _Defn):
    return Definition(Operator.OPT, (_validate(expression),))


def Star(expression: _Defn):
    return Definition(Operator.RPT, (_validate(expression), 0, -1))


def Plus(expression: _Defn):
    return Definition(Operator.RPT, (_validate(expression), 1, -1))


def Nonterminal(name: str):
    return Definition(Operator.SYM, (name,))


def And(expression: _Defn):
    return Definition(Operator.AND, (_validate(expression),))


def Not(expression: _Defn):
    return Definition(Operator.NOT, (_validate(expression),))


def Raw(expression: _Defn):
    return Definition(Operator.RAW, (_validate(expression),))


def Bind(expression: _Defn, name: str = None):
    return Definition(Operator.BND, (name, _validate(expression),))


def Evaluate(expression: _Defn):
    return Definition(Operator.EVL, (_validate(expression),))


def _make_quantified(primary, quantifier=None):
    if not quantifier:
        return _validate(primary)
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


def _make_evaluated(quantified, prefix=None):
    if not prefix:
        return _validate(quantified)
    assert len(prefix) == 1
    prefix = prefix[0]
    if prefix == '&':
        return And(quantified)
    elif prefix == '!':
        return Not(quantified)
    elif prefix == '~':
        return Raw(quantified)
    elif prefix.endswith(':'):
        name = prefix[:-1]
        return Bind(quantified, name=(name or None))
    elif prefix == '=':
        return Evaluate(quantified)
    else:
        raise Error(f'invalid prefix: {prefix!r}')


def _make_sequence(exprs):
    if len(exprs) == 1:
        return _validate(exprs[0])
    elif len(exprs) > 1:
        return Sequence(*exprs)
    else:
        raise Error(f'empty sequence: {exprs}')


def _make_choice(exprs):
    if len(exprs) == 1:
        return _validate(exprs[0])
    elif len(exprs) > 1:
        return Choice(*exprs)
    else:
        raise Error(f'empty choice: {exprs}')


def _make_group(expr):
    expr = _validate(expr)
    return expr


def _make_def(name, operator, expression):
    if operator == '<:':
        expression = Bind(expression)
    if operator == '<~':
        expression = Raw(expression)
    elif operator == '<=':
        expression = Evaluate(expression)
    return (name, expression)


def _make_grammar(*defs):
    if defs:
        start = defs[0][0]
    return Grammar(dict(defs), start=start)

def _make_start(*args):
    return args[0]

# Lexical productions do not need to go in the grammar

# Whitespace and comments
_EOF        = Bind(Not(Dot()))
_EOL        = Bind(Choice('\r\n', '\n', '\r'))
_Comment    = Raw(Sequence('#',
                           Star(Sequence(Not(_EOL), Dot())),
                           Optional(_EOL)))
_Space      = Choice(Class(' \t'), _EOL)
_Spacing    = Bind(Star(Choice(_Space, _Comment)))

# Tokens
_LEFTARROW  = Sequence('<-', _Spacing)
_RAWARROW   = Sequence('<~', _Spacing)
_SLASH      = Sequence('/', _Spacing)
_AND        = Sequence('&', _Spacing)
_NOT        = Sequence('!', _Spacing)
_TILDE      = Sequence('~', _Spacing)
_EQUAL      = Sequence('=', _Spacing)
_QUESTION   = Sequence('?', _Spacing)
_STAR       = Sequence('*', _Spacing)
_PLUS       = Sequence('+', _Spacing)
_OPEN       = Sequence('(', _Spacing)
_CLOSE      = Sequence(')', _Spacing)
_DOT        = Sequence('.', _Spacing)

# Non-recursive patterns
_Operator   = _LEFTARROW
_Char       = Choice(Sequence('\\', Dot()), Dot())
_Range      = Choice(Sequence(_Char, '-', _Char), _Char)
_Class      = Sequence(
    Bind('['),
    Raw(Star(Sequence(Not(']'), _Range))),
    Bind(']'),
    _Spacing)
_Literal    = Sequence(
    Choice(
        Sequence(Bind("'"), Raw(Star(Sequence(Not("'"), _Char))), Bind("'")),
        Sequence(Bind('"'), Raw(Star(Sequence(Not('"'), _Char))), Bind('"'))),
    _Spacing)
_IdentStart = Class('a-zA-Z_')
_IdentCont  = Class('a-zA-Z_0-9')
_Identifier = Sequence(Raw(Sequence(_IdentStart, Star(_IdentCont))), _Spacing)
_Name       = Sequence(_Identifier, Bind(Not(_Operator)), _Spacing)
_Quantifier = Choice(_QUESTION, _STAR, _PLUS)
_Binding    = Sequence(Raw(Sequence(Optional(_Name), ':')), _Spacing)
_Prefix     = Choice(_AND, _NOT, _TILDE, _Binding, _EQUAL)

PEG = Grammar(
    definitions={
        # Hierarchical syntax
        'Start':      Sequence(_Spacing,
                               Choice(Nonterminal('Grammar'),
                                      Nonterminal('Expression')),
                               _EOF),
        'Grammar':    Plus(Nonterminal('Definition')),
        'Definition': Sequence(Nonterminal('Identifier'),
                               _Operator,
                               Nonterminal('Expression')),
        'Expression': Evaluate(
            Sequence(Nonterminal('Sequence'),
                     Star(Sequence(Bind(_SLASH),
                                   Nonterminal('Sequence'))))),
        'Sequence':   Evaluate(Plus(Nonterminal('Evaluated'))),
        'Evaluated':  Sequence(Bind(Optional(_Prefix), name='prefix'),
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
        'Group':      Sequence(Bind(_OPEN),
                               Nonterminal('Expression'),
                               Bind(_CLOSE)),
        'Literal':    _Literal,
        'Class':      _Class,
        'Binding':    _Binding,
        'Prefix':     _Prefix,
        'Dot':        Bind(_DOT),
    },
    actions={
        'Start': _make_start,
        'Grammar': _make_grammar,
        'Definition': _make_def,
        'Expression': _make_choice,
        'Sequence': _make_sequence,
        'Evaluated': _make_evaluated,
        'Quantified': _make_quantified,
        'Group': _make_group,
        'Name': Nonterminal,
        'Class': Class,
        'Literal': Literal,
        'Dot': Dot,
    }
)

_parser = PackratParser(PEG)


def loads(source: str,
          flags: Flag = Flag.NONE) -> Union[Grammar, Expression]:
    """Parse the PEG at *source* and return a grammar definition."""
    m = _parser.match(source, flags=Flag.STRICT | flags)
    if not m:
        raise Error('invalid grammar')
    return m.value()


def load(source: str) -> Grammar:
    """Parse the PEG at *source* and return a grammar definition."""
    pass
