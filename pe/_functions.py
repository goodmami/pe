
from pe.grammar import compile as _pe_compile


def match(pattern: str, string: str):
    """Compile *pattern* and match *string* against it.

    Example:
        >>> import pe
        >>> pe.match(r'"-"? [1-9] [0-9]*', '-12345').value()
        '-12345'
    """
    expr = _pe_compile(pattern)
    return expr.match(string)
