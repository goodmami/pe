
import pytest

from pe.constants import NOMATCH
from pe.terms import Dot, Class
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    Peek,
    Not,
    Group,
    Rule,
    Grammar,
)

abc = Class('abc')
xyz = Class('xyz')
neg = Class('^abc')
esc = Sequence('\\', Dot())


def test_scan_Sequence():
    assert Sequence(abc).scan('aaa') == 1
    assert Sequence(abc, abc).scan('bbb') == 2
    assert Sequence(abc).scan('d') == NOMATCH


def test_match_Sequence():
    assert Sequence(abc).match('aaa').value() == 'a'
    assert Sequence(abc, abc).match('bbb').value() == 'bb'
    assert Sequence(abc).match('d') is None


def test_scan_Choice():
    assert Choice(abc).scan('aaa') == 1
    assert Choice(abc, abc).scan('aaa') == 1
    assert Choice(abc, xyz).scan('yyy') == 1
    assert Choice(abc, xyz).scan('d') == NOMATCH


def test_match_Choice():
    assert Choice(abc).match('aaa').value() == 'a'
    assert Choice(abc, abc).match('aaa').value() == 'a'
    assert Choice(abc, xyz).match('yyy').value() == 'y'
    assert Choice(abc, xyz).match('d') is None


def test_invalid_Repeat():
    with pytest.raises(ValueError):
        Repeat(abc, min=-1)
    with pytest.raises(ValueError):
        Repeat(abc, max=-2)
    with pytest.raises(ValueError):
        Repeat(abc, min=2, max=1)


def test_scan_Repeat():
    assert Repeat(abc).scan('') == 0
    assert Repeat(abc, min=1).scan('') == NOMATCH
    assert Repeat(abc).scan('aabbcc') == 6
    assert Repeat(abc, max=3).scan('aabbcc') == 3


def test_match_Repeat():
    assert Repeat(abc).match('').value() == ''
    assert Repeat(abc, min=1).match('') is None
    assert Repeat(abc).match('aabbcc').value() == 'aabbcc'
    assert Repeat(abc, max=3).match('aabbcc').value() == 'aab'


def test_scan_Optional():
    assert Optional(abc).scan('') == 0
    assert Optional(abc).scan('d') == 0
    assert Optional(abc).scan('a') == 1


def test_match_Optional():
    assert Optional(abc).match('').value() == ''
    assert Optional(abc).match('d').value() == ''
    assert Optional(abc).match('a').value() == 'a'


def test_scan_Peek():
    assert Peek(abc).scan('a') == 0
    assert Peek(abc).scan('d') == NOMATCH


def test_match_Peek():
    assert Peek(abc).match('a').value() == ''
    assert Peek(abc).match('d') is None


def test_scan_Not():
    assert Not(abc).scan('a') == NOMATCH
    assert Not(abc).scan('d') == 0


def test_match_Not():
    assert Not(abc).match('a') is None
    assert Not(abc).match('d').value() == ''


def test_scan_Group():
    assert Group(abc).scan('a') == 1
    assert Group(abc).scan('d') == NOMATCH


def test_match_Group():
    assert Group(abc).match('a').value() == 'a'
    assert Group(abc).match('d') is None


def test_scan_Rule():
    assert Rule(abc).scan('a') == 1
    assert Rule(abc).scan('d') == NOMATCH


def test_match_Rule():
    assert Rule(abc).match('a').value() == 'a'
    assert Rule(abc).match('d') is None


def test_scan_Grammar():
    assert Grammar(rules={'Start': abc}).scan('a') == 1
    assert Grammar(rules={'Start': abc}).scan('d') == NOMATCH


def test_match_Grammar():
    assert Grammar(rules={'Start': abc}).match('a').value() == 'a'
    assert Grammar(rules={'Start': abc}).match('d') is None
