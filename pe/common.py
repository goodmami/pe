
from pe.terms import (
    Dot,
    Class,
)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    NotAhead,
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

ESCAPE = Sequence('\\', DOT)
_DQCONT = Repeat(Class(r'^"\n\\'))
_SQCONT = Repeat(Class(r"^'\n\\"))
DQSTRING = Sequence('"', Repeat(_DQCONT, escape=ESCAPE), '"')
DQSTRING = Sequence('"', _DQCONT, Repeat(Choice(ESCAPE, _DQCONT)), '"')
SQSTRING = Sequence("'", Repeat(_SQCONT, escape=ESCAPE), "'")

_DQ3CONT = Sequence(NotAhead('"""'), DOT)
_SQ3CONT = Sequence(NotAhead("'''"), DOT)
DQ3STRING = Sequence('"""', Repeat(_DQ3CONT, escape=ESCAPE), '"""')
SQ3STRING = Sequence("'''", Repeat(_SQ3CONT, escape=ESCAPE), "'''")


# Whitespace

SPACE = Class('\t\n\v\f\r ')
SPACES = Repeat(SPACE, min=1)
SPACING = Repeat(SPACE)
