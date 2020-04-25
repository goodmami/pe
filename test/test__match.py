
from pe import Match
from pe.operators import Literal, Sequence, Capture, Bind, Rule
from pe.actions import Pack

One = Literal('1')
CaptureOne = Capture(Literal('1'))
OneTwo = Sequence(Literal('1'), Literal('2'))
OneCaptureTwo = Sequence(Literal('1'), Capture(Literal('2')))
OneBindTwo = Sequence(Literal('1'), Bind(Literal('2'), name='x'))
OneBindCaptureTwo = Sequence(Literal('1'),
                             Bind(Capture(Literal('2')), name='x'))
OneTwoRule = Rule(Sequence(Capture(Literal('1')), Capture(Literal('2'))),
                  action=Pack(list))


def test_Match_atom():
    m = Match('123', 0, 1, One, (), {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is One
    assert m.group(0) == '1'
    assert m.groups() == ()
    assert m.groupdict() == {}
    assert m.value() is None


def test_Match_capture_atom():
    m = Match('123', 0, 1, CaptureOne, ('1',), {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 1
    assert m.pe is CaptureOne
    assert m.group(0) == '1'
    assert m.group(1) == '1'
    assert m.groups() == ('1',)
    assert m.groupdict() == {}
    assert m.value() == '1'


def test_Match_iterable():
    m = Match('123', 0, 2, OneTwo, (), {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneTwo
    assert m.group(0) == '12'
    assert m.groups() == ()
    assert m.groupdict() == {}
    assert m.value() is None


def test_Match_capture_iterable():
    m = Match('123', 0, 2, OneCaptureTwo, ('2',), {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneCaptureTwo
    assert m.group(0) == '12'
    assert m.group(1) == '2'
    assert m.groups() == ('2',)
    assert m.groupdict() == {}
    assert m.value() == '2'


def test_Match_iterable_bind():
    m = Match('123', 0, 2, OneBindTwo, (), {'x': None})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneBindTwo
    assert m.group(0) == '12'
    assert m.group('x') is None
    assert m.groups() == ()
    assert m.groupdict() == {'x': None}
    assert m.value() is None


def test_Match_iterable_bind_capture():
    m = Match('123', 0, 2, OneBindCaptureTwo, (), {'x': '2'})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneBindCaptureTwo
    assert m.group(0) == '12'
    assert m.group('x') == '2'
    assert m.groups() == ()
    assert m.groupdict() == {'x': '2'}
    assert m.value() is None


def test_Match_iterable_rule():
    m = Match('123', 0, 2, OneTwoRule, (['1', '2'],), {})
    assert m.string == '123'
    assert m.pos == 0
    assert m.end == 2
    assert m.pe is OneTwoRule
    assert m.group(0) == '12'
    assert m.group(1) == ['1', '2']
    assert m.groups() == (['1', '2'],)
    assert m.groupdict() == {}
    assert m.value() == ['1', '2']
