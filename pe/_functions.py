
from typing import Dict, Callable

from pe.constants import Flag
from pe.core import Error, Expression
from pe.grammar import loads
from pe.packrat import PackratParser


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
    g.actions = actions
    p = make(g)
    return p


def match(pattern: str, string: str):
    """Compile *pattern* and match *string* against it.

    Example:
        >>> import pe
        >>> pe.match(r'"-"? [1-9] [0-9]*', '-12345').value()
        '-12345'
    """
    expr = compile(pattern)
    return expr.match(string)
