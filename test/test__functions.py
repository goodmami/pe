
import pe

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
