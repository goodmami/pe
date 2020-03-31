
from pe import Match
from pe.operators import Literal, Sequence, Raw, Bind

One = Literal('1')
RawOne = Raw(Literal('1'))
OneTwo = Sequence(Literal('1'), Literal('2'))
OneRawTwo = Sequence(Literal('1'), Raw(Literal('2')))
OneBindTwo = Sequence(Literal('1'), Bind(Literal('2'), name='x'))
OneBindRawTwo = Sequence(Literal('1'), Bind(Raw(Literal('2')), name='x'))


def test_Match_atom():
    m = Match('123', 0, 1, One, [], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.groups() == ()
    assert m.groupdict() == {}
    assert m.value() == None


def test_Match_raw_atom():
    m = Match('123', 0, 1, RawOne, ['1',], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is RawOne
    assert m.groups() == ('1',)
    assert m.groupdict() == {}
    assert m.value() is '1'


def test_Match_iterable():
    m = Match('123', 0, 2, OneTwo, [], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneTwo
    assert m.groups() == ()
    assert m.groupdict() == {}
    assert m.value() == []


def test_Match_raw_iterable():
    m = Match('123', 0, 2, OneRawTwo, ['2'], {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneRawTwo
    assert m.groups() == ('2',)
    assert m.groupdict() == {}
    assert m.value() == ['2',]


def test_Match_iterable_bind():
    m = Match('123', 0, 2, OneBindTwo, [], {'x': None})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneBindTwo
    assert m.groups() == ()
    assert m.groupdict() == {'x': None}
    assert m.value() == []


def test_Match_iterable_bind_raw():
    m = Match('123', 0, 2, OneBindRawTwo, [], {'x': '2'})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneBindRawTwo
    assert m.groups() == ()
    assert m.groupdict() == {'x': '2'}
    assert m.value() == []
