
from typing import Dict, Callable

from pe._constants import Flag
from pe._errors import Error
from pe._definition import Definition
from pe._parser import Parser
from pe._grammar import Grammar
from pe._parse import loads


def compile(source,
            actions: Dict[str, Callable] = None,
            parser: str = 'packrat',
            flags: Flag = Flag.OPTIMIZE) -> Parser:
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
        print(g)

    return p


def match(pattern: str,
          string: str,
          actions: Dict[str, Callable] = None,
          parser: str = 'packrat',
          flags: Flag = Flag.MEMOIZE):
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
    return expr.match(string, flags=flags)
