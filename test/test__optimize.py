
import pe
from pe.operators import (
    Literal,
    Class,
    Regex,
    Sequence,
    Choice,
    Nonterminal,
    Capture,
)
from pe._grammar import Grammar
from pe._parse import loads
from pe._optimize import optimize


def gload(s, inline=False, common=False, regex=False):
    _, original = loads(s)
    start, defmap = loads(s)
    optimized = optimize(
        Grammar(defmap, start=start),
        inline=inline,
        common=common,
        regex=regex
    )
    assert original == defmap
    return optimized


def iload(s):
    return gload(s, inline=True)


def cload(s):
    return gload(s, common=True)


def rload(s, common=False):
    return gload(s, common=common, regex=True)


def grm(d):
    return Grammar(definitions=d, start=next(iter(d)))


def test_inline():
    assert (iload(r'A <- "a"') ==
            gload(r'A <- "a"'))
    assert (iload(r'A <- B  B <- "a"') ==
            gload(r'A <- "a" B <- "a"'))
    assert (iload(r'A <- B  B <- C  C <- "a"') ==
            gload(r'A <- "a"  B <- "a"  C <- "a"'))
    assert (iload(r'A <- "a" A') ==
            gload(r'A <- "a" A'))
    assert (iload(r'A <- "a" B  B <- A') ==
            gload(r'A <- "a" A  B <- "a" B'))
    assert (iload(r'A <- "a" B  B <- "b" A') ==
            gload(r'A <- "a" "b" A  B <- "b" "a" B'))

    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.NONE).match('ab').value() is None
    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.INLINE).match('ab').value() is None
    assert pe.compile('A <- "a" B  B <- ~"b"',
                      flags=pe.NONE).match('ab').value() == 'b'
    assert pe.compile('A <- "a" B  B <- ~"b"',
                      flags=pe.INLINE).match('ab').value() == 'b'


def test_common():
    assert (cload(r'A <- "a"') ==
            gload(r'A <- "a"'))
    assert (cload(r'A <- !"a"') ==
            gload(r'A <- !"a"'))
    # single-char classes to literals
    assert (cload(r'A <- [a]') ==
            gload(r'A <- "a"'))
    # but not multi-char class
    assert (cload(r'A <- [ab]') ==
            gload(r'A <- [ab]'))
    # and not ranges
    assert (cload(r'A <- [a-c]') ==
            gload(r'A <- [a-c]'))
    # add "b" to avoid dropping the sequence
    assert (cload(r'A <- !"a" . "b"') ==
            cload(r'A <- ![a] . "b"') ==
            grm({'A': Sequence(Class('a', negate=True), Literal('b'))}))
    # now show the dropped sequence
    assert (cload(r'A <- !"a" .') ==
            cload(r'A <- ![a] .') ==
            grm({'A': Class('a', negate=True)}))
    # sequence of literals to literal
    assert (cload(r'A <- "a" "bc" "d"') ==
            gload(r'A <- "abcd"'))
    # or sequence of literals or single-char classes
    assert (cload(r'A <- "a" [b] "c"') ==
            gload(r'A <- "abc"'))
    # but not sequence with multi-char classes
    assert (cload(r'A <- "a" [bc] "d"') ==
            gload(r'A <- "a" [bc] "d"'))
    # choice of classes
    assert (cload(r'A <- [ab] / [bc]') ==
            gload(r'A <- [abc]'))
    # or choice of classes or single-char literals
    assert (cload(r'A <- [ab] / "m" / [yz]') ==
            gload(r'A <- [abmyz]'))
    # not negated classes though
    assert (cload(r'A <- (![ab] .) / "m" / [yz]') ==
            grm({'A': Choice(Class('ab', negate=True), Class('myz'))}))
    # hyphen characters are moved to start of class
    assert (cload(r'A <- [(-,] / [-.]') ==
            gload(r'A <- [-(-,.]'))


def test_regex():
    assert (rload(r'A <- "a"') ==
            grm({'A': Regex(r'a')}))
    assert (rload(r'A <- "a" [bc]') ==
            grm({'A': Regex(r'a[bc]')}))
    assert (rload(r'A <- ~("a" [bc])') ==
            grm({'A': Capture(Regex(r'a[bc]'))}))
    assert (rload(r'A <- "a" B  B <- [bc]') ==
            grm({'A': Sequence(Regex('a'), Nonterminal('B')),
                 'B': Regex('[bc]')}))
    assert (rload(r'A <- .* "a"') ==
            grm({'A': Regex(r'(?=(?P<_1>(?s:.)*))(?P=_1)a')}))
    assert (rload(r'A <- "a"* [bc]+') ==
            grm({'A': Regex(
                r'(?=(?P<_1>a*))(?P=_1)(?=(?P<_2>[bc]+))(?P=_2)')}))
    assert (rload(r'A <- "a" ~([bc] / "d")*') ==
            grm({'A': Sequence(
                Regex(r'a'),
                Capture(Regex(
                    r'(?=(?P<_2>(?:(?=(?P<_1>[bc]|d))(?P=_1))*))(?P=_2)')))}))
    assert (rload(r'A <- "ab" / "abc"') ==
            grm({'A': Regex(r'(?=(?P<_1>ab|abc))(?P=_1)')}))
    assert (rload(r'A <- "a"* / ~"b"') ==
            grm({'A': Choice(
                Regex(r'(?=(?P<_1>a*))(?P=_1)'),
                Capture(Regex(r'b')))}))


def test_regex_values():
    assert pe.compile('A <- "a" "b"',
                      flags=pe.NONE).match('ab').value() is None
    assert pe.compile('A <- "a" "b"',
                      flags=pe.REGEX).match('ab').value() is None
    assert pe.compile('A <- "a" ~"b" "c"',
                      flags=pe.NONE).match('abc').value() == 'b'
    assert pe.compile('A <- "a" ~"b" "c"',
                      flags=pe.REGEX).match('abc').value() == 'b'


def test_regex_not_dot():
    assert (rload(r'A <- !"a" .')
            == grm({'A': Regex(r'(?!a)(?s:.)')}))
    assert (rload(r'A <- !"a" .', common=True)
            == grm({'A': Regex(r'[^a]')}))
    assert (rload(r'A <- !"\\" .', common=True)
            == grm({'A': Regex(r'[^\\]')}))
    assert (rload(r'A <- ![\\] .', common=True)
            == grm({'A': Regex(r'[^\\]')}))
    assert (rload(r'A <- ![abc] .', common=True)
            == grm({'A': Regex(r'[^abc]')}))
    assert (rload(r'A <- (![abc] .)*', common=True)
            == grm({'A': Regex(r'(?=(?P<_1>[^abc]*))(?P=_1)')}))
