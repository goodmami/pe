
from typing import Dict, Callable
import re

from pe._constants import Flag
from pe._core import Error, Expression
from pe.operators import Grammar, Definition
from pe._parse import loads
from pe import (inline, merge, regex)


def compile(source,
            actions: Dict[str, Callable] = None,
            parser: str = 'packrat',
            flags: Flag = Flag.NONE) -> Expression:
    """Compile the parsing expression or grammar in *source*."""
    parsername = parser.lower()
    if parsername == 'packrat':
        from pe.packrat import PackratParser as parser
    elif parsername == 'machine':
        from pe.machine import MachineParser as parser
    else:
        raise Error(f'unsupported parser: {parser}')

    g = loads(source)
    if isinstance(g, Definition):
        g = Grammar({'Start': g})
    g.actions = actions or {}
    g.finalize()

    p = parser(g, flags=flags)

    if flags & Flag.DEBUG:
        for name, defn in g.definitions.items():
            print(name, defn)

    return p


def match(pattern: str,
          string: str,
          action: Callable = None,
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
                   action=action,
                   actions=actions,
                   parser=parser,
                   flags=Flag.OPTIMIZE)
    return expr.match(string)


_escapes = {
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
_unescapes = dict((e, u) for u, e in _escapes.items())


def escape(string: str):
    """Escape special characters for literals and character classes."""
    return re.sub('(' + '|'.join(map(re.escape, _escapes)) + ')',
                  lambda m: _escapes.get(m.group(0), m.group(0)),
                  string)


def unescape(string: str):
    """Unescape special characters for literals and character classes."""
    return re.sub('(' + '|'.join(map(re.escape, _unescapes)) + ')',
                  lambda m: _unescapes.get(m.group(0), m.group(0)),
                  string)
