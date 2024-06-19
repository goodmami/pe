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
  Start      <- Spacing (Grammar / Expression) EndOfFile
  Grammar    <- Definition+
  Definition <- Identifier defop:Operator Expression
  Operator   <- LEFTARROW / LEFTANGLE
  Expression <- Sequence (SLASH Sequence)*
  Sequence   <- Valued*
  Valued     <- (prefix:Prefix)? Quantified
  Prefix     <- AND / NOT / TILDE / Binding
  Binding    <- Identifier COLON
  Quantified <- Primary (quantifier:Quantifier)?
  Quantifier <- QUESTION / STAR / PLUS / Repeat
  Repeat     <- LEFTBRACE RepeatSpec RIGHTBRACE
  RepeatSpec <- (min:Integer)? COMMA (max:Integer)?
              / count:Integer
  Primary    <- Name / Group / Literal / Class / DOT
  Name       <- Identifier !Operator
  Group      <- OPEN Expression CLOSE

  # Lexical syntax
  Identifier <- ~(IdentStart IdentCont*) Spacing
  IdentStart <- [a-zA-Z_]
  IdentCont  <- IdentStart / [0-9]

  Literal    <- ~(['] ( !['] Char )* [']) Spacing
              / ~(["] ( !["] Char )* ["]) Spacing

  Class      <- '[' ~( !']' Range )* ']' Spacing
  Range      <- Char '-' Char / Char
  Char       <- '\\' [tnvfr"'\[\\\]]
              / '\\' Oct Oct? Oct?
              / '\\' 'x' Hex Hex
              / '\\' 'u' Hex Hex Hex Hex
              / '\\' 'U' Hex Hex Hex Hex Hex Hex Hex Hex
              / !'\\' .
  Oct        <- [0-7]
  Hex        <- [0-9a-fA-F]

  Integer    <- ~( [0-9]+ ) Spacing

  LEFTARROW  <- '<-' Spacing
  LEFTANGLE  <- '<' Space Spacing
  LEFTBRACE  <- '{' Spacing
  RIGHTBRACE <- '}' Spacing
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
  COMMA      <- ',' Spacing
  DOT        <- '.' Spacing

  Spacing    <- (Space / Comment)*
  Comment    <- '#' (!EndOfLine .)* EndOfLine
  Space      <- ' ' / '\t' / EndOfLine
  EndOfLine  <- '\r\n' / '\n' / '\r'
  EndOfFile  <- !.
"""

from functools import partial
from typing import Tuple, Dict, cast

import pe
from pe._errors import Error, ParseError, GrammarError
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
    Repeat,
    And,
    Not,
    Capture,
    Bind,
    Sequence,
    Choice,
    AutoIgnore,
    SymbolTable,
)
from pe.packrat import PackratParser
from pe.actions import Constant, Pack, Warn


def _make_literal(s):
    return Literal(pe.unescape(s[1:-1]))


def _make_class(s):
    return Class(pe.unescape(s))


def _make_quantified(primary, quantifier=None):
    if not quantifier:
        return primary
    else:
        return quantifier(primary)


def _make_binder(x):
    return lambda p, x=x: Bind(p, name=x)


def _make_valued(quantified, prefix=None):
    if not prefix:
        return quantified
    else:
        return prefix(quantified)


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


def _make_definition(identifier, expr, defop=None):
    if defop is not None:
        return (identifier, defop(expr))
    return (identifier, expr)


V = SymbolTable()

# Hierarchical syntax
V.Start = Sequence(V.Spacing, Choice(V.Grammar, V.Expression), V.EOF)
V.Grammar = Plus(V.Definition)
V.Definition = Sequence(
    V.Identifier, Bind(V.Operator, name='defop'), V.Expression
)
V.Expression = Sequence(V.Sequence, Star(Sequence(V.SLASH, V.Sequence)))
V.Sequence = Plus(V.Valued)
V.Valued = Sequence(Optional(Bind(V.Prefix, name='prefix')), V.Quantified)
V.Prefix = Choice(V.AND, V.NOT, V.TILDE, V.Binding)
V.Binding = Sequence(V.Identifier, ':', V.Spacing)
V.Quantified = Sequence(
    V.Primary, Optional(Bind(V.Quantifier, name='quantifier'))
)
V.Quantifier = Choice(V.QUESTION, V.STAR, V.PLUS, V.Repeat)
V.Repeat = Sequence(V.LEFTBRACE, V.RepeatSpec, V.RIGHTBRACE)
V.RepeatSpec = Choice(
    Sequence(
        Optional(Bind(V.Integer, name="min")),
        V.COMMA,
        Optional(Bind(V.Integer, name="max"))
    ),
    Bind(V.Integer, name="count")
)
V.Primary = Choice(V.Name, V.Group, V.Literal, V.Class, V.DOT)
V.Name = Sequence(V.Identifier, V.Spacing, Not(V.Operator))
V.Group = Sequence(V.OPEN, V.Expression, V.CLOSE)
V.Literal = Sequence(
    Choice(
        Capture(Sequence("'", Star(Sequence(Not("'"), V.Char)), "'")),
        Capture(Sequence('"', Star(Sequence(Not('"'), V.Char)), '"'))),
    V.Spacing
)
V.Class = Sequence(
    '[', Capture(Star(Sequence(Not(']'), V.Range))), ']', V.Spacing
)

# Non-recursive patterns

V.Operator = Choice(V.LEFTARROW, V.LEFTANGLE)
V.Special = Class('tnvfr"\'[]\\\\')
V.Oct = Class('0-7')
V.Hex = Class('0-9a-fA-F')
V.Octal = Sequence(V.Oct, Optional(V.Oct), Optional(V.Oct))
V.UTF8 = Sequence('x', *([V.Hex] * 2))
V.UTF16 = Sequence('u', *([V.Hex] * 4))
V.UTF32 = Sequence('U', *([V.Hex] * 8))
V.Char = Choice(
    Sequence('\\', Choice(V.Special, V.Octal, V.UTF8, V.UTF16, V.UTF32)),
    Sequence(Not('\\'), Dot())
)
V.RangeEndWarn = Literal(']')
V.Range = Choice(Sequence(V.Char, '-', Choice(V.RangeEndWarn, V.Char)), V.Char)
V.IdentStart = Class('a-zA-Z_')
V.IdentCont = Class('a-zA-Z_0-9')
V.Identifier = Sequence(
    Capture(Sequence(V.IdentStart, Star(V.IdentCont))), V.Spacing
)
V.Integer = Sequence(Capture(Plus(Class('0-9'))), V.Spacing)

# Tokens

V.LEFTARROW = Sequence('<-', V.Spacing)
V.LEFTANGLE = Sequence('<', V.Space, V.Spacing)
V.LEFTBRACE = Sequence('{', V.Spacing)
V.RIGHTBRACE = Sequence('}', V.Spacing)
V.SLASH = Sequence('/', V.Spacing)
V.AND = Sequence('&', V.Spacing)
V.NOT = Sequence('!', V.Spacing)
V.TILDE = Sequence('~', V.Spacing)
V.QUESTION = Sequence('?', V.Spacing)
V.STAR = Sequence('*', V.Spacing)
V.PLUS = Sequence('+', V.Spacing)
V.OPEN = Sequence('(', V.Spacing)
V.CLOSE = Sequence(')', V.Spacing)
V.COMMA = Sequence(',', V.Spacing)
V.DOT = Sequence('.', V.Spacing)

# Whitespace and comments

V.Spacing = Star(Choice(V.Space, V.Comment))
V.Space = Choice(Class(' \t'), V.EOL)
V.Comment = Sequence('#', Star(Sequence(Not(V.EOL), Dot())), Optional(V.EOL))
V.EOF = Not(Dot())
V.EOL = Choice('\r\n', '\n', '\r')

PEG = Grammar(
    definitions=V,
    actions={
        'Grammar': Pack(tuple),
        'Definition': _make_definition,
        'Expression': Pack(_make_prioritized),
        'Sequence': Pack(_make_sequential),
        'Valued': _make_valued,
        'AND': Constant(And),
        'NOT': Constant(Not),
        'TILDE': Constant(Capture),
        'Binding': _make_binder,
        'Quantified': _make_quantified,
        'QUESTION': Constant(Optional),
        'STAR': Constant(Star),
        'PLUS': Constant(Plus),
        'Repeat': lambda **kwargs: partial(Repeat, **kwargs),
        'Integer': int,
        'Name': Nonterminal,
        'Literal': _make_literal,
        'Class': _make_class,
        'LEFTANGLE': Constant(AutoIgnore),
        'DOT': Constant(Dot()),
        'RangeEndWarn': Warn(
            'The second character in a range may be an unescaped "]", '
            'but this is often a mistake. Silence this warning by '
            'escaping the hyphen (\\-) or the right bracket (\\]), '
            'depending on what was intended.')
    }
)

_parser = PackratParser(PEG)


def loads(source: str) -> Tuple[str, Dict[str, Definition]]:
    """Parse the PEG at *source* and return a list of definitions."""
    if not source.strip():
        raise GrammarError("empty grammar")
    try:
        m = _parser.match(source, flags=pe.STRICT | pe.MEMOIZE)
    except ParseError as exc:
        raise GrammarError("invalid grammar") from exc

    if not m:
        raise Error('invalid grammar')
    defs = m.value()
    if isinstance(defs, Definition):
        start = 'Start'
        defmap = {'Start': defs}
    else:
        assert isinstance(defs, tuple)
        defs = cast(Tuple[Tuple[str, Definition], ...], defs)
        start = defs[0][0]
        defmap = dict(defs)
    return start, defmap
