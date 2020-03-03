
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
  Prefix     <- AND / NOT / Binding
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
    elif not isinstance(arg, tuple) or not isinstance(arg[0], Operator):
        raise ValueError(f'not a valid definition: {arg!r}')
    else:
        return arg


def Dot():
    return (Operator.DOT,)


def Literal(string: str):
    return (Operator.LIT, string)


def Class(chars: str):
    return (Operator.CLS, chars)


def Regex(pattern: Union[str, Pattern], flags: int = 0):
    return (Operator.RGX, pattern, flags)


def Sequence(*expressions: _Defn):
    return (Operator.SEQ, list(map(_validate, expressions)))


def Choice(*expressions: _Defn):
    return (Operator.CHC, list(map(_validate, expressions)))


def Repeat(expression: _Defn, min: int = 0, max: int = -1):
    return (Operator.RPT, _validate(expression), min, max)


def Optional(expression: _Defn):
    return (Operator.RPT, _validate(expression), 0, 1)


def Star(expression: _Defn):
    return (Operator.RPT, _validate(expression), 0, -1)


def Plus(expression: _Defn):
    return (Operator.RPT, _validate(expression), 1, -1)


def Nonterminal(name: str):
    return (Operator.SYM, name)


def And(expression: _Defn):
    return (Operator.AND, _validate(expression))


def Not(expression: _Defn):
    return (Operator.NOT, _validate(expression))


def Bind(expression: _Defn, name: str = None):
    return (Operator.BND, name, _validate(expression))



def _make_prefixed(*args, **kwargs):
    print(args, kwargs)
    prefix, suffix = args
    primary, quantifier = suffix


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
_EOF        = Not(Dot())
_EOL        = Choice(r'\r\n', r'\n', r'\r')
_Comment    = Sequence('#', Star(Sequence(Not(_EOL), Dot())), _EOL)
_Space      = Choice(Class(' \t'), _EOL)
_Spacing    = Star(Choice(_Space, _Comment))

# Tokens
_LEFTARROW  = Sequence('<-', _Spacing)
_SLASH      = Sequence('/', _Spacing)
_AND        = Sequence('&', _Spacing)
_NOT        = Sequence('!', _Spacing)
_QUESTION   = Sequence('?', _Spacing)
_STAR       = Sequence('*', _Spacing)
_PLUS       = Sequence('+', _Spacing)
_OPEN       = Sequence('(', _Spacing)
_CLOSE      = Sequence(')', _Spacing)
_DOT        = Sequence('.', _Spacing)
_COLON      = Sequence(':', _Spacing)

# Non-recursive patterns
_Char       = Choice(Sequence('\\', Dot()), Dot())
_Range      = Choice(Sequence(_Char, '-', _Char), _Char)
_Class      = Sequence('[', Star(Sequence(Not(']'), _Range)), ']')
_Literal    = Choice(Sequence("'", Star(Sequence(Not("'"), _Char)), "'"),
                     Sequence('"', Star(Sequence(Not('"'), _Char)), '"'))
_IdentStart = Class('a-zA-Z_')
_IdentCont  = Class('a-zA-Z_0-9')
_Identifier = Sequence(_IdentStart, Star(_IdentCont), _Spacing)
_Name       = Sequence(_Identifier, Not(_LEFTARROW))
_Quantifier = Choice(_QUESTION, _STAR, _PLUS)
_Binding    = Sequence(Optional(_Name), _COLON)
_Prefix     = Choice(_AND, _NOT, _Binding)

PEG = Grammar(
    definitions={
        # Hierarchical syntax
        'Start':      Sequence(_Spacing,
                               Choice(Nonterminal('Expression'),
                                      Nonterminal('Grammar')),
                               _EOF),
        'Grammar':    Plus(Nonterminal('Definition')),
        'Definition': Sequence(Nonterminal('Identifier'),
                               Bind(_LEFTARROW),
                               Nonterminal('Expression')),
        'Expression': Sequence(Nonterminal('Sequence'),
                               Star(Sequence(_SLASH,
                                             Nonterminal('Sequence')))),
        'Sequence':   Star(Nonterminal('Prefixed')),
        'Prefixed':   Sequence(Optional(_Prefix), Nonterminal('Quantified')),
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
        'Quantifier': _Quantifier,
        'Binding':    _Binding,
        'Prefix':     _Prefix,
        'Dot':        Bind(_DOT),

    },
    actions={
        'Dot': lambda: (Op.DOT,),
        'Class': lambda s: (Op.CLS, s[1:-1]),
        'Literal': lambda s: (Op.LIT, s[1:-1]),
        'Name': lambda s: (Op.SYM, s),
        'Group': _make_group,
        'Prefixed': _make_prefixed,
        'Sequence': lambda xs: (Op.SEQ, xs),
        'Expression': lambda xs: (Op.CHC, xs),
        'Definition': _make_def,
        'Grammar': _make_grammar,
    }
)

_parser = PackratParser(PEG)

def loads(source: str) -> Grammar:
    m = _parser.match(s)
    if not m:
        raise Error('invalid grammar')
    return m.value()


# _DOT = Dot()

# # Whitespace and comments

# EndOfFile  = Not(_DOT)
# EndOfLine  = Chc(r'\r\n', r'\n', r'\r')
# Comment    = Seq('#', Rpt(Seq(Not(EndOfLine), _DOT)), EndOfLine)
# Space      = Chc(' ', r'\t', EndOfLine)
# Spacing    = Rpt(Chc(Space, Comment))

# # Lexical syntax

# LEFTARROW  = Seq('<-', Spacing)
# RAWARROW   = Seq('<~', Spacing)
# SLASH      = Seq('/', Spacing)
# AND        = Seq('&', Spacing)
# NOT        = Seq('!', Spacing)
# QUESTION   = Seq('?', Spacing)
# STAR       = Seq('*', Spacing)
# PLUS       = Seq('+', Spacing)
# OPEN       = Seq('(', Spacing)
# CLOSE      = Seq(')', Spacing)
# DOT        = Seq('.', Spacing)
# COLON      = Seq(':', Spacing)

# Char       = Chc(Seq('\\', _DOT), _DOT)
# Range      = Chc(Seq(Char, '-', Char), Char)
# Class      = Seq('[', Rpt(Seq(Not(']'), Range)), ']')
# Literal    = Chc(
#     Seq("'", Rpt(Seq(Not("'"), Char)), "'"),
#     Seq('"', Rpt(Seq(Not('"'), Char)), '"'))

# IdentStart = Cls('a-zA-Z_')
# IdentCont  = Chc(IdentStart, Cls('0-9'))
# Identifier = Seq(IdentStart, Rpt(IdentCont), Spacing)

# Operator   = Chc(LEFTARROW, RAWARROW)
# Name       = Seq(Identifier, Not(Operator))
# Quantifier = Chc(QUESTION, STAR, PLUS)
# Binding    = Seq(Opt(Name), COLON)
# Prefix     = Chc(AND, NOT, Binding)

# G['Dot']        = Bind(DOT)
# G['Class']      = Class
# G['Literal']    = Literal
# G['Name']       = Name

# # Hierarchical syntax

# G['Group']      = Seq(OPEN, G['Expression'], CLOSE)
# G['Primary']    = Chc(G['Name'], G['Group'], G['Literal'], G['Class'], G['Dot'])
# G['Quantified'] = Seq(G['Primary'], Opt(Quantifier))
# G['Prefixed']   = Seq(Opt(Prefix), G['Quantified'])
# G['Sequence']   = Rpt(G['Prefixed'])
# G['Expression'] = Seq(G['Sequence'], Rpt(Seq(SLASH, G['Sequence'])))
# G['Definition'] = Seq(Identifier, Operator, G['Expression'])
# G['Grammar']    = Rpt(G['Definition'], min=1)
# G['Start']      = Seq(Spacing, Chc(G['Expression'], G['Grammar']), EndOfFile)

# # Semantic actions

# G.update_actions({
#     'Dot': lambda: (Op.DOT,),
#     'Class': lambda s: (Op.CLS, s[1:-1]),
#     'Literal': lambda s: (Op.LIT, s[1:-1]),
#     'Name': lambda s: (Op.SYM, s),
#     'Group': _make_group,
#     'Prefixed': _make_prefixed,
#     'Sequence': lambda xs: (Op.SEQ, xs),
#     'Expression': lambda xs: (Op.CHC, xs),
#     'Definition': _make_def,
#     'Grammar': _make_grammar,
# })
