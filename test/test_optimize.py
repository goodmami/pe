
import pe
from pe.constants import Flag
from pe.core import Grammar
from pe.grammar import loads, Regex, Sequence, Nonterminal
from pe.optimize import inline, merge, regex


def iload(s): return inline(loads(s))
def mload(s): return merge(loads(s))
def rload(s): return regex(loads(s))
def grm(d): return Grammar(definitions=d, start=next(iter(d)))


def test_inline():
    assert (iload(r'A <- "a"') ==
            loads(r'A <- "a"'))
    assert (iload(r'A <- B  B <- "a"') ==
            loads(r'A <- "a" B <- "a"'))
    assert (iload(r'A <- B  B <- C  C <- "a"') ==
            loads(r'A <- "a"  B <- "a"  C <- "a"'))
    assert (iload(r'A <- "a" A') ==
            loads(r'A <- "a" A'))
    assert (iload(r'A <- "a" B  B <- A') ==
            loads(r'A <- "a" A  B <- "a" B'))
    assert (iload(r'A <- "a" B  B <- "b" A') ==
            loads(r'A <- "a" "b" A  B <- "b" "a" B'))

    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=Flag.NONE).match('ab').value() == ('a', 'b')
    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=Flag.INLINE).match('ab').value() == ('a', 'b')


def test_merge():
    assert (mload(r'A <- "a"') ==
            loads(r'A <- "a"'))
    assert (mload(r'A <- "a" "b"') ==
            loads(r'A <- "ab"'))
    assert (mload(r'A <- "a" [b]') ==
            loads(r'A <- "ab"'))
    assert (mload(r'A <- "a" [bc]') ==
            loads(r'A <- "a" [bc]'))
    assert (mload(r'A <- "a" / "b"') ==
            loads(r'A <- [ab]'))
    assert (mload(r'A <- "a" / [bc]') ==
            loads(r'A <- [abc]'))
    assert (mload(r'A <- "a"* / [bc]') ==
            loads(r'A <- "a"* / [bc]'))

    assert pe.compile('A <- "a" "b"',
                      flags=Flag.NONE).match('ab').value() == ('a', 'b')
    # Currently failing
    # assert pe.compile('A <- "a" "b"',
    #                   flags=Flag.MERGE).match('ab').value() == ('a', 'b')
    # assert pe.compile('A <- :("a" "b")',
    #                   flags=Flag.MERGE).match('ab').value() == ('a', 'b')


def test_regex():
    assert (rload(r'A <- "a"') ==
            grm({'A': Regex(r'a')}))
    assert (rload(r'A <- "a" [bc]') ==
            grm({'A': Regex(r'a[bc]')}))
    assert (rload(r'A <- "a" B  B <- [bc]') ==
            grm({'A': Sequence(Regex('a'), Nonterminal('B')),
                 'B': Regex('[bc]')}))
    assert (rload(r'A <- "a"* [bc]+') ==
            grm({'A': Regex(r'(?:a)*(?:[bc])+')}))
    assert (rload(r'A <- "a" ([bc] / "d")*') ==
            grm({'A': Regex(r'a(?:(?:[bc]|d))*')}))

    assert (rload(r'A <- !"a" .') ==
            grm({'A': Regex(r'[^a]')}))
    assert (rload(r'A <- ![abc] .') ==
            grm({'A': Regex(r'[^abc]')}))
    assert (rload(r'A <- (![abc] .)*') ==
            grm({'A': Regex(r'(?:[^abc])*')}))

    assert pe.compile('A <- "a" :"b" "c"',
                      flags=Flag.NONE).match('abc').value() == ('a', 'c')
    assert pe.compile('A <- "a" :"b" "c"',
                      flags=Flag.REGEX).match('abc').value() == ('a', 'c')
