
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
com = Class(',')
neg = Class('^abc')
esc = Sequence('\\', Dot())


def test_scan_Sequence():
    assert Sequence(abc).scan('aaa') == 1
    assert Sequence(abc, abc).scan('bbb') == 2
    assert Sequence(abc).scan('d') == NOMATCH


def test_scan_Choice():
    assert Choice(abc).scan('aaa') == 1
    assert Choice(abc, abc).scan('aaa') == 1
    assert Choice(abc, xyz).scan('yyy') == 1
    assert Choice(abc, xyz).scan('d') == NOMATCH


def test_scan_Repeat():
    assert Repeat(abc).scan('') == 0
    assert Repeat(abc, min=1).scan('') == NOMATCH
    assert Repeat(abc).scan('aabbcc') == 6
    assert Repeat(abc, max=3).scan('aabbcc') == 3

    with pytest.raises(ValueError):
        Repeat(abc, min=-1)
    with pytest.raises(ValueError):
        Repeat(abc, max=-2)
    with pytest.raises(ValueError):
        Repeat(abc, min=2, max=1)


def test_scan_Repeat_delimited():
    rpt = Repeat(abc, delimiter=com)
    assert rpt.scan('') == 0
    assert rpt.scan('a') == 1
    assert rpt.scan('aa') == 1
    assert rpt.scan('a,a') == 3
    assert rpt.scan(',a') == 0
    assert rpt.scan('a,aa') == 3
    assert rpt.scan('a,a,,') == 3
    assert rpt.scan('a,a,a') == 5
    assert Repeat(abc, max=2, delimiter=com).scan('a,a,a') == 3


def test_scan_Optional():
    assert Optional(abc).scan('') == 0
    assert Optional(abc).scan('d') == 0
    assert Optional(abc).scan('a') == 1


def test_scan_Peek():
    assert Peek(abc).scan('a') == 0
    assert Peek(abc).scan('d') == NOMATCH


def test_scan_Not():
    assert Not(abc).scan('a') == NOMATCH
    assert Not(abc).scan('d') == 0


def test_scan_Group():
    assert Group(abc).scan('a') == 1
    assert Group(abc).scan('d') == NOMATCH


def test_scan_Rule():
    assert Rule(abc).scan('a') == 1
    assert Rule(abc).scan('d') == NOMATCH


def test_scan_Grammar():
    assert Grammar(rules={'Start': abc}).scan('a') == 1
    assert Grammar(rules={'Start': abc}).scan('d') == NOMATCH


