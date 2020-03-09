
from pe.core import Match
from pe.packrat import Terminal, Sequence, Bind

One = Terminal('1')
NullOne = Bind(One)
OneTwo = Sequence(One, Terminal('2'))


def test_noniterable_Match_empty_args():
    m = Match('123', 0, 1, NullOne, [], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is NullOne
    assert m.groups() == ()
    assert m.groupdict() == {}
    assert m.value() is None


def test_iterable_Match_empty_args():
    m = Match('123', 0, 2, OneTwo, [], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneTwo
    assert m.groups() == ()
    assert m.groupdict() == {}
    assert m.value() == []


def test_noniterable_Match_with_args():
    m = Match('123', 0, 1, One, [1], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == (1,)
    assert m.groupdict() == {}
    assert m.value() == 1


def test_iterable_Match_with_args():
    m = Match('123', 0, 2, OneTwo, [1, 2], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneTwo
    assert m.groups() == (1, 2)
    assert m.groupdict() == {}
    assert m.value() == [1, 2]


def test_noniterable_Match_with_kwargs():
    m = Match('123', 0, 1, NullOne, [], kwargs={'num': 1})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is NullOne
    assert m.groups() == ()
    assert m.groupdict() == {'num': 1}
    assert m.value() is None


def test_iterable_Match_with_kwargs():
    m = Match('123', 0, 2, OneTwo, [], kwargs={'num': (1, 2)})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneTwo
    assert m.groups() == ()
    assert m.groupdict() == {'num': (1, 2)}
    assert m.value() == []

