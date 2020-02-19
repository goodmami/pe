
from pe.terms import (
    Dot,
    Class,
)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Until,
    Optional,
)

DOT = Dot()

# Numbers

DIGIT = Class('0-9')
DIGITS = Repeat(DIGIT, min=1)
UNSIGNED_INTEGER = Choice('0', Sequence(Class('1-9'), Repeat(DIGIT)))
INTEGER = Sequence(Optional(Class('-+')), UNSIGNED_INTEGER)
SIGNED_INTEGER = Sequence(Class('-+'), UNSIGNED_INTEGER)

FLOAT_FRACTION = Sequence('.', DIGITS)
FLOAT_EXPONENT = Sequence(Class('eE'), INTEGER)
FLOAT = Sequence(INTEGER, Optional(FLOAT_FRACTION), Optional(FLOAT_EXPONENT))

# Strings
ESCAPE = Sequence('\\', DOT)
DQSTRING = Sequence('"', Until(Class('"\n'), escape=ESCAPE), '"')
SQSTRING = Sequence("'", Until(Class("'\n"), escape=ESCAPE), "'")

DQ3STRING = Sequence('"""', Until('"""', escape=ESCAPE), '"""')
SQ3STRING = Sequence("'''", Until("'''", escape=ESCAPE), "'''")


# Whitespace

SPACE = Class('\t\n\v\f\r ')
SPACES = Repeat(SPACE, min=1)
SPACING = Repeat(SPACE)
