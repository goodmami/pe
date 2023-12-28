
import pytest

import pe


@pytest.mark.parametrize('parser', ['packrat', 'machine', 'machine-python'])
def test_capture_choice(parser):
    assert pe.match(r'~("a" / "b" / "c")', 'c', parser=parser) is not None
    assert pe.match(r'~("a" / "b" / "c")', 'b', parser=parser) is not None
    assert pe.match(r'~("a" / "b" / "c")', 'a', parser=parser) is not None


@pytest.mark.parametrize('parser', ['packrat', 'machine', 'machine-python'])
def test_multi_range_charclass(parser):
    p = pe.compile(
        r'''
        Start    <- ["] CHAR* ["]
        CHAR     <- [ !#-\[\]-\U0010ffff]
        ''',
        parser=parser,
    )
    assert p.match('""') is not None
    assert p.match('"a"') is not None
    assert p.match('"ab"') is not None
    assert p.match('"1a"') is not None
    assert p.match('"1"') is not None
    assert p.match('"\U0010ffff"') is not None
    assert p.match('"a1"') is not None


@pytest.mark.parametrize('parser', ['packrat', 'machine', 'machine-python'])
def test_capture_repeated(parser):
    m1 = pe.match('"a"+', 'aaa', parser=parser)
    assert m1.group() == 'aaa'
    assert m1.groups() == ()
    m2 = pe.match('~"a"+', 'aaa', parser=parser)
    assert m2.group() == 'aaa'
    assert m2.groups() == ('aaa',)
    m3 = pe.match('(~"a")+', 'aaa', parser=parser)
    assert m3.group() == 'aaa'
    assert m3.groups() == ('a', 'a', 'a')
