
import pytest

import pe
from pe.packrat import PackratParser
from pe.machine import MachineParser


def test_compile_default():
    p = pe.compile(r'"a"')
    assert isinstance(p, PackratParser)
    assert p.match('a')


def test_compile_parser():
    p = pe.compile(r'"a"', parser='packrat')
    assert isinstance(p, PackratParser)
    assert p.match('a')

    p = pe.compile(r'"a"', parser='machine')
    assert isinstance(p, MachineParser)
    assert p.match('a')


def test_compile_actions():
    p = pe.compile(r'~"1"', actions={'Start': int})
    assert p.match('1').value() == 1


def test_match():
    assert pe.match(r'"a"', 'a')
    assert not pe.match(r'"a"', 'b')


def test_match_strict():
    assert pe.match(r'"a"', 'a', flags=pe.STRICT)
    with pytest.raises(pe.ParseError):
        pe.match(r'"a"', 'b', flags=pe.STRICT)


def test_escape():
    assert pe.escape('\t') == '\\t'
    assert pe.escape('\n') == '\\n'
    assert pe.escape('\v') == '\\v'
    assert pe.escape('\f') == '\\f'
    assert pe.escape('\r') == '\\r'
    assert pe.escape('"') == '\\"'
    assert pe.escape("'") == "\\'"
    assert pe.escape('-') == '\\-'
    assert pe.escape('[') == '\\['
    assert pe.escape('\\') == '\\\\'
    assert pe.escape(']') == '\\]'


def test_unescape():
    assert pe.unescape('\\t') == '\t'
    assert pe.unescape('\\n') == '\n'
    assert pe.unescape('\\v') == '\v'
    assert pe.unescape('\\f') == '\f'
    assert pe.unescape('\\r') == '\r'
    assert pe.unescape('\\"') == '"'
    assert pe.unescape("\\'") == "'"
    assert pe.unescape('\\-') == '-'
    assert pe.unescape('\\[') == '['
    assert pe.unescape('\\\\') == '\\'
    assert pe.unescape('\\]') == ']'
    assert pe.unescape('\\100') == '@'
    assert pe.unescape('\\x40') == '@'
    assert pe.unescape('\\u0040') == '@'
    assert pe.unescape('\\U00000040') == '@'
    # multiple escape sequences are not multibyte sequences
    assert pe.unescape('\\xef\\xbc\\xa0') == '\xef\xbc\xa0'
    assert pe.unescape('\\xef\\xbc\\xa0') != b'\xef\xbc\xa0'.decode('utf-8')
