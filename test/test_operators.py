import pytest

from pe._constants import Operator as Op
from pe._definition import Definition as Def
from pe.operators import (
    Dot,
    Literal,
    Class,
    Regex,
    Sequence,
    Choice,
    Optional,
    Star,
    Plus,
    Repeat,
    Nonterminal,
    And,
    Not,
    Capture,
    Bind,
    AutoIgnore,
)


def test_Dot():
    assert Dot() == Def(Op.DOT, ())


def test_Literal():
    assert Literal('foo') == Def(Op.LIT, ('foo',))


def test_Class():
    assert Class('foo') == Def(
        Op.CLS,
        ([('f', None), ('o', None), ('o', None)], False)
    )
    assert Class('f') == Def(Op.CLS, ([('f', None)], False))
    assert Class('f', negate=True) == Def(Op.CLS, ([('f', None)], True))


def test_Regex():
    assert Regex('foo') == Def(Op.RGX, ('foo', 0))
    assert Regex('foo', flags=1) == Def(Op.RGX, ('foo', 1))


def test_Sequence():
    assert (Sequence(Literal('a'), Dot())
            == Def(Op.SEQ, ([Literal('a'), Dot()],)))
    assert Sequence('foo', 'bar') == Sequence(Literal('foo'), Literal('bar'))
    # simple optimizations
    assert Sequence(Dot()) == Dot()
    assert Sequence(Sequence('a', 'b'), 'c') == Sequence('a', 'b', 'c')


def test_Choice():
    assert (Choice(Literal('a'), Dot())
            == Def(Op.CHC, ([Literal('a'), Dot()],)))
    assert Choice('foo', 'bar') == Choice(Literal('foo'), Literal('bar'))
    # simple optimizations
    assert Choice(Dot()) == Dot()
    assert Choice(Choice('a', 'b'), 'c') == Choice('a', 'b', 'c')


def test_Optional():
    assert Optional(Dot()) == Def(Op.OPT, (Dot(),))
    assert Optional('foo') == Optional(Literal('foo'))


def test_Star():
    assert Star(Dot()) == Def(Op.STR, (Dot(),))
    assert Star('foo') == Star(Literal('foo'))


def test_Plus():
    assert Plus(Dot()) == Def(Op.PLS, (Dot(),))
    assert Plus('foo') == Plus(Literal('foo'))


def test_Repeat():
    assert Repeat(Dot()) == Def(Op.RPT, (Dot(), 0, -1))
    assert Repeat(Dot(), 2) == Def(Op.RPT, (Dot(), 2, 2))
    assert Repeat(Dot(), count=2) == Def(Op.RPT, (Dot(), 2, 2))
    assert Repeat(Dot(), min=1) == Def(Op.RPT, (Dot(), 1, -1))
    assert Repeat(Dot(), max=1) == Def(Op.RPT, (Dot(), 0, 1))
    assert Repeat(Dot(), min=1, max=2) == Def(Op.RPT, (Dot(), 1, 2))
    with pytest.raises(ValueError):
        Repeat(Dot(), min=-1)
    with pytest.raises(ValueError):
        Repeat(Dot(), count=2, max=3)


def test_Nonterminal():
    assert Nonterminal('A') == Def(Op.SYM, ('A',))


def test_And():
    assert And(Dot()) == Def(Op.AND, (Dot(),))
    assert And('foo') == And(Literal('foo'))


def test_Not():
    assert Not(Dot()) == Def(Op.NOT, (Dot(),))
    assert Not('foo') == Not(Literal('foo'))


def test_Capture():
    assert Capture(Dot()) == Def(Op.CAP, (Dot(),))
    assert Capture('foo') == Capture(Literal('foo'))


def test_Bind():
    assert Bind(Dot(), name='x') == Def(Op.BND, (Dot(), 'x'))
    assert Bind('foo', name='bar') == Bind(Literal('foo'), name='bar')


def test_AutoIgnore():
    assert AutoIgnore(Dot()) == Def(Op.IGN, (Dot(),))
    assert AutoIgnore('foo') == AutoIgnore(Literal('foo'))
