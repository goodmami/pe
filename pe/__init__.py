
from pe._constants import Flag
NONE     = Flag.NONE
DEBUG    = Flag.DEBUG
STRICT   = Flag.STRICT
MEMOIZE  = Flag.MEMOIZE
INLINE   = Flag.INLINE
MERGE    = Flag.MERGE
REGEX    = Flag.REGEX
OPTIMIZE = Flag.OPTIMIZE

from pe._core import Error, ParseError, Match, Expression
from pe._functions import compile, match, escape, unescape



