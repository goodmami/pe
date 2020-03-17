
import pe
from pe.grammar import loads
from pe.merge import optimize

def mload(s): return optimize(loads(s))

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
                      flags=pe.NONE).match('ab').value() == ('a', 'b')
    # Currently failing
    # assert pe.compile('A <- "a" "b"',
    #                   flags=pe.MERGE).match('ab').value() == ('a', 'b')
    # assert pe.compile('A <- :("a" "b")',
    #                   flags=pe.MERGE).match('ab').value() == ('a', 'b')

    assert pe.compile('A <- x:("a" / "b")',
                      actions={'A': lambda x: x},
                      flags=pe.NONE).match('a').value() == ['a']
    # assert pe.compile('A <- x:("a" / "b")',
    #                   actions={'A': lambda x: x},
    #                   flags=pe.MERGE).match('a').value() == ['a']

