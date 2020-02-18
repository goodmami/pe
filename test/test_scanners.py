
from pe.constants import NOMATCH
from pe.scanners import (
    Literal,
    Class,
    Run,
    Until,
    Pattern,
)


def test_Literal():
    assert Literal('a')('a') == 1
    assert Literal('a')('aa') == 1
    assert Literal('a')('b') == NOMATCH
    assert Literal('a')('a', pos=1) == NOMATCH
    assert Literal('a')('ab', pos=1) == NOMATCH
    assert Literal('b')('ab') == NOMATCH
    assert Literal('b')('ab', pos=1) == 2
    assert Literal('abc')('abcabc') == 3
    assert Literal('abc')('abcabc', pos=1) == NOMATCH
    assert Literal('abc')('abcabc', pos=3) == 6


def test_Class():
    assert Class('ab')('a') == 1
    assert Class('ab')('aa') == 1
    assert Class('ab')('b') == 1
    assert Class('ab')('a', pos=1) == NOMATCH
    assert Class('ab')('ab', pos=1) == 2
    assert Class('ab', negate=True)('ab') == NOMATCH
    assert Class('ab', negate=True)('c') == 1
    assert Class('ab', negate=True)('a', pos=1) == NOMATCH


def test_Run():
    assert Run(Literal('a'))('a') == 1
    assert Run(Literal('a'))('aa') == 2
    assert Run(Literal('a'))('aaa') == 3
    assert Run(Class('ab'))('abc') == 2

def test_Run_min_max():
    assert Run(Literal('a'), min=2)('a') == NOMATCH
    assert Run(Literal('a'), min=2)('aa') == 2
    assert Run(Literal('a'), min=2)('aaa') == 3
    assert Run(Literal('a'), max=2)('a') == 1
    assert Run(Literal('a'), max=2)('aa') == 2
    assert Run(Literal('a'), max=2)('aaa') == 2

# def test_Run_escape():
#     assert Run(Literal('a'), escape='\\')('aba') == 1
#     assert Run(Literal('a'), escape='\\')('a\\ba') == 4

# def test_Run_until():
#     assert Run(Class('abc'), until='aaa')('abcbaaa') == 4
#     assert Run(Class('abc'), until='aaa')('abcbaaa', pos=4) == 4
#     assert Run(Class('abc'), until='aaa')('abcbaaa', pos=5) == 7

def test_Until():
    assert Until('b')('b') == 0
    assert Until('b')('ab') == 1
    assert Until('b')('aab') == 2
    assert Until('b')('b') == 0
    assert Until('b')('\\bb') == 1
    assert Until('b', escape='\\')('\\bb') == 2

    assert Until(Literal('b'))('ab') == 1
    assert Until(Class('abc'))('xyzb') == 3


def test_Pattern():
    assert Pattern(Literal('a'))('a') == 1
    assert Pattern(Literal('a'))('aa') == 1
    assert Pattern(Literal('a'))('b') == NOMATCH

    assert Pattern(Literal('a'), Literal('b'))('a') == NOMATCH
    assert Pattern(Literal('a'), Literal('b'))('b') == NOMATCH
    assert Pattern(Literal('a'), Literal('b'))('ab') == 2

    assert Pattern(Literal('a'), Class('bc'))('a') == NOMATCH
    assert Pattern(Literal('a'), Class('bc'))('b') == NOMATCH
    assert Pattern(Literal('a'), Class('bc'))('ab') == 2
    assert Pattern(Literal('a'), Class('bc'))('ac') == 2
    assert Pattern(Literal('a'), Class('bc'))('ad') == NOMATCH
    assert Pattern(Literal('a'), Class('bc'))('abc') == 2
