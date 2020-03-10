
from pe.constants import Operator as Op
from pe.core import (
    Definition as Def,
    Grammar as Grammar,
)
from pe.grammar import (
    loads,
    Dot,
    Literal,
    Class,
    Regex,
    Sequence,
    Choice,
    Repeat,
    Optional,
    Star,
    Plus,
    Nonterminal,
    And,
    Not,
    Raw,
    Bind,
    Evaluate,
)


def test_Dot():
    assert Dot() == Def(Op.DOT, ())


def test_Literal():
    assert Literal('foo') == Def(Op.LIT, ('foo',))


def test_Class():
    assert Class('foo') == Def(Op.CLS, ('foo',))
    # simple optimizations
    assert Class('f') == Def(Op.LIT, ('f',))


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


def test_Repeat():
    assert Repeat(Dot()) == Def(Op.RPT, (Def(Op.DOT, ()), 0, -1))
    assert Repeat(Dot(), min=1) == Def(Op.RPT, (Def(Op.DOT, ()), 1, -1))
    assert Repeat(Dot(), max=3) == Def(Op.RPT, (Def(Op.DOT, ()), 0, 3))
    assert Repeat(Dot(), min=1, max=3) == Def(Op.RPT, (Def(Op.DOT, ()), 1, 3))
    assert Repeat('foo') == Repeat(Literal('foo'))


def test_Optional():
    assert Optional(Dot()) == Def(Op.OPT, (Def(Op.DOT, ()),))
    assert Optional('foo') == Optional(Literal('foo'))


def test_Star():
    assert Star(Dot()) == Def(Op.RPT, (Def(Op.DOT, ()), 0, -1))
    assert Star('foo') == Star(Literal('foo'))


def test_Plus():
    assert Plus(Dot()) == Def(Op.RPT, (Def(Op.DOT, ()), 1, -1))
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
    assert Raw('foo') == Def(Op.RAW, (Def(Op.LIT, ('foo',)),))


def test_Bind():
    assert Bind(Dot()) == Def(Op.BND, (None, Def(Op.DOT, ())))
    assert Bind(Dot(), name='x') == Def(Op.BND, ('x', Def(Op.DOT, ())))
    assert Bind('foo') == Bind(Literal('foo'))
    assert Bind('foo', name='bar') == Bind(Literal('foo'), name='bar')


def test_Evaluate():
    assert Evaluate(Dot()) == Def(Op.EVL, (Def(Op.DOT, ()),))
    assert Evaluate('foo') == Evaluate(Literal('foo'))


def test_loads_dot():
    assert loads('.') == Dot()
    assert loads('.  # comment') == Dot()


def test_loads_literal():
    assert loads('"foo"') == Literal('foo')
    from pe.grammar import _parser
    assert loads('"foo"  # comment') == Literal('foo')


def test_loads_class():
    assert loads('[xyz]') == Class('xyz')
    assert loads('[xyz]  # comment') == Class('xyz')


def test_loads_nonterminal():
    assert loads('foo') == Nonterminal('foo')
    assert loads('foo  # comment') == Nonterminal('foo')


def test_loads_optional():
    assert loads('"a"?') == Optional('a')
    assert loads('"a"?  # comment') == Optional('a')


def test_loads_star():
    assert loads('"a"*') == Star('a')
    assert loads('"a"*  # comment') == Star('a')


def test_loads_plus():
    assert loads('"a"+') == Plus('a')
    assert loads('"a"+  # comment') == Plus('a')


def test_loads_sequence():
    assert loads('"a" "b"') == Sequence('a', 'b')
    assert loads('"a" "b"  # comment') == Sequence('a', 'b')


def test_loads_choice():
    assert loads('"a" / "b"') == Choice('a', 'b')
    assert loads('"a" / "b"  # comment') == Choice('a', 'b')


def test_loads_and():
    assert loads('&"a"') == And('a')
    assert loads('&"a"  # comment') == And('a')


def test_loads_not():
    assert loads('!"a"') == Not('a')
    assert loads('!"a"  # comment') == Not('a')


def test_loads_raw():
    assert loads('~"a"') == Raw('a')
    assert loads('~"a"  # comment') == Raw('a')


def test_loads_bind():
    assert loads(':"a"') == Bind('a')
    assert loads(':"a"  # comment') == Bind('a')
    assert loads('x:"a"') == Bind('a', name='x')
    assert loads('x:"a"  # comment') == Bind('a', name='x')
    assert loads('x :"a"') == Sequence(Nonterminal('x'), Bind('a'))


def test_loads_raw():
    assert loads('="a"') == Evaluate('a')
    assert loads('="a"  # comment') == Evaluate('a')


def Grm(dfns):
    return Grammar(definitions=dfns, start=next(iter(dfns)))


def test_loads_def():
    assert loads('A <- "a"') == Grm({'A': Literal('a')})
    assert loads('A <- "a"  # comment') == Grm({'A': Literal('a')})
    assert loads('A <- "a" "b"') == Grm({'A': Sequence('a', 'b')})
    assert loads('A <- "a" B <- "b"') == Grm({'A': Literal('a'),
                                              'B': Literal('b')})
    assert loads('''
        A   <- "a" Bee
        Bee <- "b"
    ''') == Grm({'A': Sequence('a', Nonterminal('Bee')),
                 'Bee': Literal('b')})
