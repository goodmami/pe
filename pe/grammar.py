
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
  Sequence   <- Evaluated*
  Evaluated  <- Prefix? Quantified
  Prefix     <- AND / NOT / TILDE / Binding
  Binding    <- Name? :COLON
  Quantified <- Primary Quantifier?
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

from typing import Union, Pattern
from operator import itemgetter

from pe.constants import Operator
from pe.core import Expression, Definition, Grammar
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



def _make_quantified(primary, quantifier=None):
    if quantifier is None:
        return primary
    elif quantifier == '?':
        return Optional(primary)
    elif quantifier == '*':
        return Star(primary)
    elif quantifier == '+':
        return Plus(primary)
    else:
        raise Error(f'invalid quantifier: {quantifier!r}')


def _make_evaluated(*args):
    if len(args) == 1:
        return args[0]
    else:
        print(args)
        prefix, quantified = args
        if prefix == '&':
            return And(quantified)
        if prefix == '!':
            return Not(quantified)
        if prefix == '~':
            return Raw(quantified)
        elif prefix.endswith(':'):
            name = prefix[:-1]
            return Bind(quantified, name=(name or None))
        else:
            raise Error(f'invalid prefix: {prefix!r}')


def _make_sequence(xs):
    print('seq', xs)
    return Sequence(*xs)


def _make_group(*args, **kwargs):
    print(args, kwargs)


def _make_def(name, operator, expression):
    return (name, Rule(expression))


def _make_grammar(*defs):
    if defs:
        start = defs[0][0]
    return Grammar(defs, start=start)


# Lexical productions do not need to go in the grammar

# Whitespace and comments
_EOF        = Bind(Not(Dot()))
_EOL        = Bind(Choice(r'\r\n', r'\n', r'\r'))
_Comment    = Raw(Sequence('#', Star(Sequence(Not(_EOL), Dot())), _EOL))
_Space      = Choice(Class(' \t'), _EOL)
_Spacing    = Bind(Star(Choice(_Space, _Comment)))

# Tokens
_LEFTARROW  = Sequence('<-', _Spacing)
_RAWARROW   = Sequence('<~', _Spacing)
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
_COLON      = Sequence(':', _Spacing)

# Non-recursive patterns
_Operator   = Choice(_LEFTARROW, _RAWARROW)
_Char       = Choice(Sequence('\\', Dot()), Dot())
_Range      = Choice(Sequence(_Char, '-', _Char), _Char)
_Class      = Raw(Sequence('[', Star(Sequence(Not(']'), _Range)), ']'))
_Literal    = Raw(Choice(Sequence("'", Star(Sequence(Not("'"), _Char)), "'"),
                         Sequence('"', Star(Sequence(Not('"'), _Char)), '"')))
_IdentStart = Class('a-zA-Z_')
_IdentCont  = Class('a-zA-Z_0-9')
_Identifier = Sequence(Raw(Sequence(_IdentStart, Star(_IdentCont))), _Spacing)
_Name       = Sequence(_Identifier, Bind(Not(_Operator)))
_Quantifier = Choice(_QUESTION, _STAR, _PLUS)
_Binding    = Raw(Sequence(Optional(_Name), _COLON))
_Prefix     = Choice(_AND, _NOT, _TILDE, _Binding)

PEG = Grammar(
    definitions={
        # Hierarchical syntax
        'Start':      Sequence(_Spacing,
                               Choice(Nonterminal('Expression'),
                                      Nonterminal('Grammar')),
                               _EOF),
        'Grammar':    Plus(Nonterminal('Definition')),
        'Definition': Sequence(Nonterminal('Identifier'),
                               _Operator,
                               Nonterminal('Expression')),
        'Expression': Sequence(Nonterminal('Sequence'),
                               Star(Sequence(_SLASH,
                                             Nonterminal('Sequence')))),
        'Sequence':   Star(Nonterminal('Evaluated')),
        'Evaluated':  Sequence(Optional(_Prefix), Nonterminal('Quantified')),
        'Quantified': Sequence(Nonterminal('Primary'), Optional(_Quantifier)),
        'Primary':    Choice(Nonterminal('Name'),
                             Nonterminal('Group'),
                             Nonterminal('Literal'),
                             Nonterminal('Class'),
                             Nonterminal('Dot')),
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
        'Dot': lambda: Dot(),
        'Class': lambda s: Class(s[1:-1]),
        'Literal': lambda s: Literal(s[1:-1]),
        'Name': lambda s: Nonterminal(s),
        'Group': _make_group,
        'Quantified': _make_quantified,
        'Evaluated': _make_evaluated,
        'Sequence': _make_sequence,
        'Expression': lambda xs: Choice(*xs),
        'Definition': _make_def,
        'Grammar': _make_grammar,
    }
)

_parser = PackratParser(PEG)


def loads(source: str) -> Union[Grammar, Expression]:
    """Parse the PEG at *source* and return a grammar definition."""
    m = _parser.match(source)
    if not m:
        raise Error('invalid grammar')
    return m.value()


def load(source: str) -> Grammar:
    """Parse the PEG at *source* and return a grammar definition."""
    pass
