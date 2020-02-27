
from pe.constants import NOMATCH
from pe.terms import (
    Dot,
    Literal,
    Class,
    Regex,
)


def test_scan_Dot():
    assert Dot().scan('aaa') == 1
    assert Dot().scan('   ') == 1
    assert Dot().scan('') == NOMATCH


def test_match_Dot():
    assert Dot().match('aaa').groups() == ('a',)
    assert Dot().match('   ').groups() == (' ',)
    assert Dot().match('') is None


def test_scan_Literal():
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


def test_match_Literal():
    assert Literal('a').match('a').groups() == ('a',)
    assert Literal('a').match('aa').groups() == ('a',)
    assert Literal('a').match('b') is None
    assert Literal('a').match('a', pos=1) is None
    assert Literal('a').match('ab', pos=1) is None
    assert Literal('b').match('ab') is None
    assert Literal('b').match('ab', pos=1).groups() == ('b',)
    assert Literal('abc').match('abcabc').groups() == ('abc',)
    assert Literal('abc').match('abcabc', pos=1) is None
    assert Literal('abc').match('abcabc', pos=3).groups() == ('abc',)


def test_scan_Class():
    assert Class('ab').scan('a') == 1
    assert Class('ab').scan('aa') == 1
    assert Class('ab').scan('b') == 1
    assert Class('ab').scan('a', pos=1) == NOMATCH
    assert Class('ab').scan('ab', pos=1) == 2
    assert Class('^ab').scan('ab') == NOMATCH
    assert Class('^ab').scan('c') == 1
    assert Class('^ab').scan('a', pos=1) == NOMATCH


def test_match_Class():
    assert Class('ab').match('a').groups() == ('a',)
    assert Class('ab').match('aa').groups() == ('a',)
    assert Class('ab').match('b').groups() == ('b',)
    assert Class('ab').match('a', pos=1) is None
    assert Class('ab').match('ab', pos=1).groups() == ('b',)
    assert Class('^ab').match('ab') is None
    assert Class('^ab').match('c').groups() == ('c',)
    assert Class('^ab').match('a', pos=1) is None


def test_scan_Regex():
    assert Regex('a').scan('a') == 1
    assert Regex('a*').scan('aaa') == 3
    assert Regex('a|b').scan('b') == 1


def test_match_Regex():
    assert Regex('a').match('a').groups() == ('a',)
    assert Regex('a*').match('aaa').groups() == ('aaa',)
    assert Regex('a|b').match('b').groups() == ('b',)
