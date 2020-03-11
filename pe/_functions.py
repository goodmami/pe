
from typing import Dict, Callable

from pe.constants import Flag
from pe.core import Error, Expression
from pe.grammar import loads
from pe.packrat import PackratParser
from pe.optimize import inline, merge, regex


def compile(source,
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
    g.actions = actions or {}

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


def match(pattern: str, string: str, flags: Flag = Flag.NONE):
    """Compile *pattern* and match *string* against it.

    Example:
        >>> import pe
        >>> pe.match(r'"-"? [1-9] [0-9]*', '-12345').value()
        '-12345'
    """
    expr = compile(pattern, flags=Flag.OPTIMIZE)
    return expr.match(string)
