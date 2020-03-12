
from typing import Dict, Callable
import re

from pe.constants import Flag
from pe.core import Error, Expression, Grammar, Definition
from pe.grammar import loads
from pe.packrat import PackratParser
from pe.optimize import inline, merge, regex


def compile(source,
            action: Callable = None,
            actions: Dict[str, Callable] = None,
            parser: str = 'packrat',
            flags: Flag = Flag.NONE) -> Expression:
    """Compile the parsing expression or grammar in *source*."""
    parsername = parser.lower()
    if parsername == 'packrat':
        make = PackratParser
    else:
        raise Error(f'unsupported parser: {parser}')
    g = loads(source, flags=flags)
    if isinstance(g, Definition):
        g = Grammar({'Start': g})
    g.actions = actions or {}
    if action:
        g.actions[g.start] = action

    if flags & Flag.INLINE:
        g = inline(g)
    if flags & Flag.MERGE:
        g = merge(g)
    if flags & Flag.REGEX:
        g = regex(g)
    if flags & Flag.DEBUG:
        for name, defn in g.definitions.items():
            print(name, defn)

    p = make(g)
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


def escape(s: str):
    """Escape special characters for literals and character classes."""
    return re.sub('(' + '|'.join(map(re.escape, _escapes)) + ')',
                  lambda m: _escapes.get(m.group(0), m.group(0)),
                  s)


def unescape(s: str):
    """Unescape special characters for literals and character classes."""
    return re.sub('(' + '|'.join(map(re.escape, _unescapes)) + ')',
                  lambda m: _unescapes.get(m.group(0), m.group(0)),
                  s)
