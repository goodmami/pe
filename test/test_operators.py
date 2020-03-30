
from pe._constants import Operator as Op
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
    assert Dot() == Def(Op.DOT, ())


def test_Literal():
    assert Literal('foo') == Def(Op.LIT, ('foo',))


def test_Class():
    assert Class('foo') == Def(Op.CLS, ('foo',))
    assert Class('f') == Def(Op.CLS, ('f',))


def test_Regex():
    assert Regex('foo') == Def(Op.RGX, ('foo', 0))
    assert Regex('foo', flags=1) == Def(Op.RGX, ('foo', 1))


def test_Sequence():
    assert Sequence(Literal('a'), Dot()) == Def(Op.SEQ, ([Def(Op.LIT, ('a',)),
                                                          Def(Op.DOT, ())],))
    assert Sequence('foo', 'bar') == Sequence(Literal('foo'), Literal('bar'))
    # simple optimizations
    assert Sequence(Dot()) == Def(Op.DOT, ())
    assert Sequence(Sequence('a', 'b'), 'c') == Sequence('a', 'b', 'c')

def test_Choice():
    assert Choice(Literal('a'), Dot()) == Def(Op.CHC, ([Def(Op.LIT, ('a',)),
                                                        Def(Op.DOT, ())],))
    assert Choice('foo', 'bar') == Choice(Literal('foo'), Literal('bar'))
    # simple optimizations
    assert Choice(Dot()) == Def(Op.DOT, ())
    assert Choice(Choice('a', 'b'), 'c') == Choice('a', 'b', 'c')


def test_Optional():
    assert Optional(Dot()) == Def(Op.OPT, (Def(Op.DOT, ()),))
    assert Optional('foo') == Optional(Literal('foo'))


def test_Star():
    assert Star(Dot()) == Def(Op.STR, (Def(Op.DOT, ()),))
    assert Star('foo') == Star(Literal('foo'))


def test_Plus():
    assert Plus(Dot()) == Def(Op.PLS, (Def(Op.DOT, ()),))
    assert Plus('foo') == Plus(Literal('foo'))


def test_Nonterminal():
    assert Nonterminal('A') == Def(Op.SYM, ('A',))


def test_And():
    assert And(Dot()) == Def(Op.AND, (Def(Op.DOT, ()),))
    assert And('foo') == And(Literal('foo'))


def test_Not():
    assert Not(Dot()) == Def(Op.NOT, (Def(Op.DOT, ()),))
    assert Not('foo') == Not(Literal('foo'))


def test_Raw():
    assert Raw(Dot()) == Def(Op.RAW, (Def(Op.DOT, ()),))
    assert Raw('foo') == Raw(Literal('foo'))


def test_Bind():
    assert Bind(Dot(), name='x') == Def(Op.BND, (Def(Op.DOT, ()), 'x'))
    assert Bind('foo', name='bar') == Bind(Literal('foo'), name='bar')


def test_Discard():
    assert Discard(Dot()) == Def(Op.DIS, (Def(Op.DOT, ()),))
    assert Discard('foo') == Discard(Literal('foo'))
