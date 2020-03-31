
from pe._definition import Definition
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
)
from pe._parse import loads

def test_loads_dot():
    assert loads('.') == Dot()
    assert loads('.  # comment') == Dot()


def test_loads_literal():
    assert loads('"foo"') == Literal('foo')
    assert loads('"foo"  # comment') == Literal('foo')
    assert loads('"\\t"') == Literal('\t')
    assert loads('"\\n"') == Literal('\n')
    assert loads('"\\v"') == Literal('\v')
    assert loads('"\\f"') == Literal('\f')
    assert loads('"\\r"') == Literal('\r')
    assert loads('"\\""') == Literal('"')
    assert loads("'\\''") == Literal("'")
    assert loads("'\\-'") == Literal("-")
    assert loads("'\\['") == Literal("[")
    assert loads("'\\\\'") == Literal("\\")
    assert loads("'\\]'") == Literal("]")
    # TODO: octal, utf8, utf16, utf32, escape errors


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
    assert loads('x:"a"') == Bind('a', name='x')
    assert loads('x:"a"  # comment') == Bind('a', name='x')
    assert loads('x: "a"') == Bind('a', name='x')
    assert loads('x : "a"') == Bind('a', name='x')


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
