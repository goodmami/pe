
import pytest

from pe.constants import NOMATCH
from pe.terms import Dot, Class
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    Ahead,
    NotAhead,
    Group,
    Nonterminal,
    Grammar,
)

abc = Class('abc')
xyz = Class('xyz')
com = Class(',')
neg = Class('^abc')
esc = Sequence('\\', Dot())


def test_Sequence():
    assert Sequence(abc).scan('aaa') == 1
    assert Sequence(abc, abc).scan('bbb') == 2
    assert Sequence(abc).scan('d') == NOMATCH


def test_Choice():
    assert Choice(abc).scan('aaa') == 1
    assert Choice(abc, abc).scan('aaa') == 1
    assert Choice(abc, xyz).scan('yyy') == 1
    assert Choice(abc, xyz).scan('d') == NOMATCH


def test_Repeat():
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


def test_Repeat_delimited():
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


def test_Repeat_escaped():
    rpt = Repeat(neg, escape=esc)
    assert rpt.scan('') == 0
    assert rpt.scan('a') == 0
    assert rpt.scan('z') == 1
    assert rpt.scan('zz') == 2
    assert rpt.scan('\\az') == 3
    assert rpt.scan('z\\aa') == 3


def test_Repeat_delimited_escaped():
    rpt = Repeat(abc, delimiter=com, escape=esc)
    assert rpt.scan('') == 0
    assert rpt.scan('a') == 1
    assert rpt.scan('aa') == 1
    assert rpt.scan('a\\a') == 3
    assert rpt.scan('a\\,a') == 3
    assert rpt.scan('a\\a,a') == 5
    assert rpt.scan('\\d') == 2
    assert rpt.scan('\\d,a') == 2
    assert rpt.scan('\\da,d') == 3
    assert rpt.scan('\\,a') == 3
    rpt = Repeat(abc, min=1, delimiter=com, escape=esc)
    assert rpt.scan('') == NOMATCH
    assert rpt.scan('a') == 1
    assert rpt.scan('a\\d') == 3
    assert rpt.scan('\\da') == 3
    assert rpt.scan('\\d') == NOMATCH
    assert rpt.scan('\\da\\d,\\da') == 9


def test_Repeat_escaped():
    assert Repeat(neg, escape=esc).scan('') == 0
    assert Repeat(neg, escape=esc).scan('a') == 0
    assert Repeat(neg, escape=esc).scan('z') == 1
    assert Repeat(neg, escape=esc).scan('zz') == 2
    assert Repeat(neg, escape=esc).scan('\\az') == 3
    assert Repeat(neg, escape=esc).scan('z\\aa') == 3


def test_Optional():
    pass


def test_Ahead():
    pass


def test_NotAhead():
    pass


def test_Group():
    pass


def test_Nonterminal():
    pass


def test_Grammar():
    pass


