
from pe.constants import NOMATCH
from pe.terms import (
    Dot,
    Literal,
    Class,
    Regex,
)


def test_Dot():
    assert Dot().scan('aaa') == 1
    assert Dot().scan('   ') == 1
    assert Dot().scan('') == NOMATCH


def test_Literal():
    assert Literal('a').scan('a') == 1
    assert Literal('a').scan('aa') == 1
    assert Literal('a').scan('b') == NOMATCH
    assert Literal('a').scan('a', pos=1) == NOMATCH
    assert Literal('a').scan('ab', pos=1) == NOMATCH
    assert Literal('b').scan('ab') == NOMATCH
    assert Literal('b').scan('ab', pos=1) == 2
    assert Literal('abc').scan('abcabc') == 3
    assert Literal('abc').scan('abcabc', pos=1) == NOMATCH
    assert Literal('abc').scan('abcabc', pos=3) == 6


def test_Class():
    assert Class('ab').scan('a') == 1
    assert Class('ab').scan('aa') == 1
    assert Class('ab').scan('b') == 1
    assert Class('ab').scan('a', pos=1) == NOMATCH
    assert Class('ab').scan('ab', pos=1) == 2
    assert Class('^ab').scan('ab') == NOMATCH
    assert Class('^ab').scan('c') == 1
    assert Class('^ab').scan('a', pos=1) == NOMATCH


def test_Regex():
    assert Regex('a').scan('a') == 1
    assert Regex('a*').scan('aaa') == 3
    assert Regex('a|b').scan('b') == 1

# def test_Run():
#     assert Run(Literal('a')).scan('a') == 1
#     assert Run(Literal('a')).scan('aa') == 2
#     assert Run(Literal('a')).scan('aaa') == 3
#     assert Run(Class('ab')).scan('abc') == 2

# def test_Run_min_max():
#     assert Run(Literal('a'), min=2).scan('a') == NOMATCH
#     assert Run(Literal('a'), min=2).scan('aa') == 2
#     assert Run(Literal('a'), min=2).scan('aaa') == 3
#     assert Run(Literal('a'), max=2).scan('a') == 1
#     assert Run(Literal('a'), max=2).scan('aa') == 2
#     assert Run(Literal('a'), max=2).scan('aaa') == 2

# def test_Run_escape():
#     assert Run(Literal('a'), escape='\\').scan('aba') == 1
#     assert Run(Literal('a'), escape='\\').scan('a\\ba') == 4

# def test_Run_until():
#     assert Run(Class('abc'), until='aaa').scan('abcbaaa') == 4
#     assert Run(Class('abc'), until='aaa').scan('abcbaaa', pos=4) == 4
#     assert Run(Class('abc'), until='aaa').scan('abcbaaa', pos=5) == 7

# def test_Until():
#     assert Until('b').scan('b') == 0
#     assert Until('b').scan('ab') == 1
#     assert Until('b').scan('aab') == 2
#     assert Until('b').scan('b') == 0
#     assert Until('b').scan('\\bb') == 1
#     assert Until('b', escape='\\').scan('\\bb') == 2

#     assert Until(Literal('b')).scan('ab') == 1
#     assert Until(Class('abc')).scan('xyzb') == 3


# def test_Pattern():
#     assert Pattern(Literal('a')).scan('a') == 1
#     assert Pattern(Literal('a')).scan('aa') == 1
#     assert Pattern(Literal('a')).scan('b') == NOMATCH

#     assert Pattern(Literal('a'), Literal('b')).scan('a') == NOMATCH
#     assert Pattern(Literal('a'), Literal('b')).scan('b') == NOMATCH
#     assert Pattern(Literal('a'), Literal('b')).scan('ab') == 2

#     assert Pattern(Literal('a'), Class('bc')).scan('a') == NOMATCH
#     assert Pattern(Literal('a'), Class('bc')).scan('b') == NOMATCH
#     assert Pattern(Literal('a'), Class('bc')).scan('ab') == 2
#     assert Pattern(Literal('a'), Class('bc')).scan('ac') == 2
#     assert Pattern(Literal('a'), Class('bc')).scan('ad') == NOMATCH
#     assert Pattern(Literal('a'), Class('bc')).scan('abc') == 2
