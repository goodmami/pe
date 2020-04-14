
from pe._meta import __version__  # noqa: F401
from pe._constants import Flag
from pe._errors import Error, GrammarError, ParseError
from pe._grammar import Grammar
from pe._match import Match
from pe._escape import escape, unescape
from pe._parser import Parser
from pe._functions import compile, match


NONE = Flag.NONE
DEBUG = Flag.DEBUG
STRICT = Flag.STRICT
MEMOIZE = Flag.MEMOIZE
INLINE = Flag.INLINE
REGEX = Flag.REGEX
OPTIMIZE = Flag.OPTIMIZE


__all__ = [
    'NONE',
    'DEBUG',
    'STRICT',
    'MEMOIZE',
    'OPTIMIZE',
    'Error',
    'GrammarError',
    'ParseError',
    'Grammar',
    'Match',
    'escape',
    'unescape',
    'Parser',
    'compile',
    'match',
]
