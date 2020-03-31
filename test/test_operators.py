
from pe._constants import Operator as Op, Value
from pe._definition import Definition as Def
from pe._grammar import Grammar
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
    Nonterminal,
    And,
    Not,
    Raw,
    Bind,
    Discard,
)


def test_Dot():
    assert Dot() == Def(Op.DOT, (), Value.ATOMIC)


def test_Literal():
    assert Literal('foo') == Def(Op.LIT, ('foo',), Value.ATOMIC)


def test_Class():
    assert Class('foo') == Def(Op.CLS, ('foo',), Value.ATOMIC)
    assert Class('f') == Def(Op.CLS, ('f',), Value.ATOMIC)


def test_Regex():
    assert Regex('foo') == Def(Op.RGX, ('foo', 0), Value.ATOMIC)
    assert Regex('foo', flags=1) == Def(Op.RGX, ('foo', 1), Value.ATOMIC)


def test_Sequence():
    assert (Sequence(Literal('a'), Dot())
            == Def(Op.SEQ, ([Literal('a'), Dot()],), Value.ITERABLE))
    assert Sequence('foo', 'bar') == Sequence(Literal('foo'), Literal('bar'))
    # simple optimizations
    assert Sequence(Dot()) == Dot()
    assert Sequence(Sequence('a', 'b'), 'c') == Sequence('a', 'b', 'c')

def test_Choice():
    assert (Choice(Literal('a'), Dot())
            == Def(Op.CHC, ([Literal('a'), Dot()],), Value.ITERABLE))
    assert Choice('foo', 'bar') == Choice(Literal('foo'), Literal('bar'))
    # simple optimizations
    assert Choice(Dot()) == Dot()
    assert Choice(Choice('a', 'b'), 'c') == Choice('a', 'b', 'c')


def test_Optional():
    assert Optional(Dot()) == Def(Op.OPT, (Dot(),), Value.ITERABLE)
    assert Optional('foo') == Optional(Literal('foo'))


def test_Star():
    assert Star(Dot()) == Def(Op.STR, (Dot(),), Value.ITERABLE)
    assert Star('foo') == Star(Literal('foo'))


def test_Plus():
    assert Plus(Dot()) == Def(Op.PLS, (Dot(),), Value.ITERABLE)
    assert Plus('foo') == Plus(Literal('foo'))


def test_Nonterminal():
    assert Nonterminal('A') == Def(Op.SYM, ('A',), Value.DEFERRED)


def test_And():
    assert And(Dot()) == Def(Op.AND, (Dot(),), Value.EMPTY)
    assert And('foo') == And(Literal('foo'))


def test_Not():
    assert Not(Dot()) == Def(Op.NOT, (Dot(),), Value.EMPTY)
    assert Not('foo') == Not(Literal('foo'))


def test_Raw():
    assert Raw(Dot()) == Def(Op.RAW, (Dot(),), Value.ATOMIC)
    assert Raw('foo') == Raw(Literal('foo'))


def test_Bind():
    assert Bind(Dot(), name='x') == Def(Op.BND, (Dot(), 'x'), Value.EMPTY)
    assert Bind('foo', name='bar') == Bind(Literal('foo'), name='bar')


def test_Discard():
    assert Discard(Dot()) == Def(Op.DIS, (Dot(),), Value.EMPTY)
    assert Discard('foo') == Discard(Literal('foo'))
