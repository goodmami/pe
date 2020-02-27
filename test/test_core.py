
from pe.core import Match
from pe.terms import Literal

One = Literal('1')


def test_Match_no_args():
    m = Match('123', 0, 1, One)
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == ()
    assert m.groupdict() == {}


def test_Match_with_empty_args():
    m = Match('123', 0, 1, One, [])
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == ()
    assert m.groupdict() == {}


def test_Match_with_args():
    m = Match('123', 0, 1, One, [1])
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == (1,)
    assert m.groupdict() == {}


def test_Match_with_kwargs():
    m = Match('123', 0, 1, One, kwargs={'num': 1})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == ()
    assert m.groupdict() == {'num': 1}


def test_Match_with_args_and_kwargs():
    m = Match('123', 0, 1, One)
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == ()
    assert m.groupdict() == {}


def test_Match_no_group():
    a = Literal('a')
    m = a.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is a
    assert m.groups() == ()
    assert m.groupdict() == {}


def test_Match_group():
    b = Group(Literal('b'))
    m = b.match('abc', pos=1)
    assert m.string == 'abc'
    assert m.pos == 1
    assert m.end == 2
    assert m.pe is b
    assert m.groups() == ('b',)
    assert m.groupdict() == {}


def test_Match_sequence_no_group():
    ab = Sequence(Literal('a'), Literal('b'))
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert m.groups() == ()
    assert m.groupdict() == {}


def test_Match_sequence_partial_groups():
    ab = Sequence(Literal('a'), Group(Literal('b')))
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert m.groups() == ('b',)
    assert m.groupdict() == {}


def test_Match_sequence_full_groups():
    ab = Sequence(Group(Literal('a')), Group(Literal('b')))
    m = ab.match('abc')
    assert m.string == 'abc'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is ab
    assert m.groups() == ('a', 'b')
    assert m.groupdict() == {}


# def test_Match_values():
#     a = Literal('a')
#     b = Literal('b')
#     assert a.match('a').value() == 'a'
#     assert Group(a).match('a').value() == 'a'
#     assert Group(Group(a)).match('a').value() == ['a']
#     assert Sequence(a).match('a').value() == 'a'
#     assert Group(Sequence(a)).match('a').value() == 'a'
#     assert Sequence(Group(a)).match('a').value() == 'a'
#     assert Sequence(a, Group(b)).match('ab').value() == 'b'
#     assert Sequence(Group(a), Group(b)).match('ab').value() == 'a'
#     assert Sequence(Sequence(Group(a))).match('a').value() == 'a'
