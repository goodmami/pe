
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

dot = Dot()

# Numbers

digit = Class('0-9')
digits = Repeat(digit)

unsigned_integer = Choice('0', Sequence(Class('1-9'), digits))
integer = Sequence(Optional(Class('-+')), unsigned_integer)
signed_integer = Sequence(Class('-+'), unsigned_integer)

float_fraction = Sequence('.', digits)
float_exponent = Sequence(Class('eE'), integer)
float = Sequence(integer, Optional(float_fraction), Optional(float_exponent))

# Strings
dqstring = Sequence('"', Until(Class('"\n'), escape='\\'), '"')
sqstring = Sequence("'", Until(Class('"\n'), escape='\\'), '"')

dq3string = Sequence('"""', Until('"""', escape='\\'), '"""')
sq3string = Sequence("'''", Until("'''", escape='\\'), "'''")


# Whitespace

Space = Class('\t\n\v\f\r ')
Spaces = Repeat(Space, min=1)
Spacing = Repeat(Space)
