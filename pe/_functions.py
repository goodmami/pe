
from pe.core import Expression
from pe.grammar import PEG


def compile(source) -> Expression:
    """Compile the parsing expression or grammar in *source*."""
    m = PEG.match(source)
    return m.value()


def match(pattern: str, string: str):
    """Compile *pattern* and match *string* against it.

    Example:
        >>> import pe
        >>> pe.match(r'"-"? [1-9] [0-9]*', '-12345').value()
        '-12345'
    """
    expr = compile(pattern)
    return expr.match(string)
