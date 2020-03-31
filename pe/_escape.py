
from typing import List, Dict, Match as reMatch

import re

_escapes: Dict[str, str] = {
    '\t' : '\\t',
    '\n' : '\\n',
    '\v' : '\\v',
    '\f' : '\\f',
    '\r' : '\\r',
    '"'  : '\\"',
    "'"  : "\\'",
    '-'  : '\\-',
    '['  : '\\[',
    '\\' : '\\\\',
    ']'  : '\\]',
}
_escape_re = re.compile(
    '({})'.format(
        '|'.join(map(re.escape, _escapes))))
_codepoint_escapes: List[str] = [
    '\\\\[0-7]{1,3}',       # oct
    '\\\\x[0-9a-fA-F]{2}',  # hex
    '\\\\u[0-9a-fA-F]{4}',  # hex
    '\\\\U[0-9a-fA-F]{8}',  # hex
]
_unescapes = dict((e, u) for u, e in _escapes.items())
_unescape_re = re.compile(
    '({})'.format(
        '|'.join(list(map(re.escape, _unescapes))
                 + _codepoint_escapes)))


def escape(string: str, ignore=''):
    """Escape special characters for literals and character classes."""

    def _escape(m: reMatch):
        c = m.group(0)
        if c in ignore:
            return c
        else:
            return _escapes.get(m.group(0), m.group(0))

    return _escape_re.sub(_escape, string)


def _unescape(m: reMatch):
    x = m.group(0)
    c = _unescapes.get(x)
    if not c:
        if x[1].isdigit():
            c = chr(int(x[1:], 8))
        else:
            c = chr(int(x[2:], 16))
    return c

def unescape(string: str):
    """Unescape special characters for literals and character classes."""
    return _unescape_re.sub(_unescape, string)
