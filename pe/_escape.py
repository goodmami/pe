
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


def escape(string: str):
    """Escape special characters for literals and character classes."""
    return re.sub('(' + '|'.join(map(re.escape, _escapes)) + ')',
                  lambda m: _escapes.get(m.group(0), m.group(0)),
                  string)


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
