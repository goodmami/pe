
from pe.terms import (
    Dot,
    Class,
)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    Not,
)

DOT = Dot()

# Numbers

DIGIT = Class('0-9')
DIGITS = Repeat(DIGIT, min=1)
UNSIGNED_INTEGER = Choice('0', Sequence(Class('1-9'), Repeat(DIGIT)))
INTEGER = Sequence(Optional(Class('-+')), UNSIGNED_INTEGER)
SIGNED_INTEGER = Sequence(Class('-+'), UNSIGNED_INTEGER)

FLOAT_FRACTION = Sequence('.', DIGITS)
FLOAT_EXPONENT = Sequence(Class('eE'), Optional(Class('-+')), Repeat(DIGIT))
FLOAT = Sequence(INTEGER, Optional(FLOAT_FRACTION), Optional(FLOAT_EXPONENT))

ESCAPE = Sequence('\\', DOT)
_DQCONT = Repeat(Class(r'^"\n\\'))
_SQCONT = Repeat(Class(r"^'\n\\"))
DQSTRING = Sequence('"', _DQCONT, Repeat(Choice(ESCAPE, _DQCONT)), '"')
SQSTRING = Sequence("'", _SQCONT, Repeat(Choice(ESCAPE, _SQCONT)), "'")

_DQ3CONT = Sequence(Not('"""'), DOT)
_SQ3CONT = Sequence(Not("'''"), DOT)
DQ3STRING = Sequence('"""', Repeat(_DQ3CONT, delimiter=Repeat(ESCAPE)), '"""')
SQ3STRING = Sequence("'''", Repeat(_SQ3CONT, delimiter=Repeat(ESCAPE)), "'''")


# Whitespace

SPACE = Class('\t\n\v\f\r ')
SPACES = Repeat(SPACE, min=1)
SPACING = Repeat(SPACE)
