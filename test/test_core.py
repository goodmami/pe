
from pe.core import Match
from pe.terms import Literal
from pe.expressions import Group, Sequence


def test_Match_no_group():
    a = Literal('a')
    m = a.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is a
    assert m.value() == 'a'


def test_Match_group():
    b = Group(Literal('b'))
    m = b.match('abc', pos=1)
    assert m.string == 'abc'
    assert m.pos == 1
    assert m.end == 2
    assert m.pe is b
    assert m.value() == ['b']


def test_Match_sequence_no_group():
    ab = Sequence(Literal('a'), Literal('b'))
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert m.value() == 'ab'


def test_Match_sequence_partial_groups():
    ab = Sequence(Literal('a'), Group(Literal('b')))
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert m.value() == ['b']


def test_Match_sequence_full_groups():
    ab = Sequence(Group(Literal('a')), Group(Literal('b')))
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert m.value() == ['a', 'b']


def test_Match_values():
    a = Literal('a')
    b = Literal('b')
    assert a.match('a').value() == 'a'
    assert Group(a).match('a').value() == ['a']
    assert Group(Group(a)).match('a').value() == [['a']]
    # assert Group(Literal('1'), action=int).match('1').value() == 1
    assert Sequence(a).match('a').value() == 'a'
    assert Group(Sequence(a)).match('a').value() == ['a']
    assert Sequence(Group(a)).match('a').value() == ['a']
    assert Sequence(a, Group(b)).match('ab').value() == ['b']
    assert Sequence(Group(a), Group(b)).match('ab').value() == ['a', 'b']
    assert Sequence(Sequence(Group(a))).match('a').value() == ['a']
