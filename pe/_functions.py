
from typing import List, Dict, Callable, Match as reMatch
import re

from pe._constants import Flag
from pe._core import Error, Definition
from pe._parser import Parser
from pe._grammar import Grammar
from pe._parse import loads
from pe import (inline, merge, regex)


def compile(source,
            actions: Dict[str, Callable] = None,
            parser: str = 'packrat',
            flags: Flag = Flag.NONE) -> Parser:
    """Compile the parsing expression or grammar in *source*."""
    parsername = parser.lower()
    if parsername == 'packrat':
        from pe.packrat import PackratParser as parser_class
    elif parsername == 'machine':
        from pe.machine import MachineParser as parser_class  # type: ignore
    else:
        raise Error(f'unsupported parser: {parser}')

    if isinstance(source, (Definition, Grammar)):
        g = source
    elif hasattr(source, 'read'):
        g = loads(source.read())
    else:
        g = loads(source)

    if isinstance(g, Definition):
        g = Grammar({'Start': g})

    g.actions = actions or {}
    g.finalize()

    p = parser_class(g, flags=flags)

    if flags & Flag.DEBUG:
        for name, defn in g.definitions.items():
            print(name, defn)

    return p


def match(pattern: str,
          string: str,
          actions: Dict[str, Callable] = None,
          parser: str = 'packrat',
          flags: Flag = Flag.NONE):
    """Compile *pattern* and match *string* against it.

    Example:
        >>> import pe
        >>> pe.match(r'"-"? [1-9] [0-9]*', '-12345').value()
        '-12345'
    """
    expr = compile(pattern,
                   actions=actions,
                   parser=parser,
                   flags=Flag.OPTIMIZE)
    return expr.match(string)


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
