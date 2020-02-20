
from pe.core import Match
from pe import Literal, Group, Sequence


def test_Match():
    a = Literal('a')
    m = a.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is a
    assert m.matches == []
    assert m.value() == 'a'

    b = Group(Literal('b'))
    m = b.match('abc', pos=1)
    assert m.string == 'abc'
    assert m.pos == 1
    assert m.end == 2
    assert m.pe is b
    assert len(m.matches) == 1
    assert m.value() == 'b'

    ab = Sequence(a, b)
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert len(m.matches) == 2
    assert m.value() == ['b']

def test_Match_values():
    a = Literal('a')
    b = Literal('b')
    assert a.match('a').value() == 'a'
    assert Group(a).match('a').value() == 'a'
    assert Group(Group(a)).match('a').value() == ['a']
    assert Group(Literal('1'), action=int).match('1').value() == 1
    assert Sequence(a).match('a').value() == 'a'
    assert Group(Sequence(a)).match('a').value() == 'a'
    assert Sequence(Group(a)).match('a').value() == ['a']
    assert Sequence(a, Group(b)).match('ab').value() == ['b']
    assert Sequence(Group(a), Group(b)).match('ab').value() == ['a', 'b']
    assert Sequence(Sequence(Group(a))).match('a').value() == [['a']]
