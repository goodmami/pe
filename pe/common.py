
from pe.scanners import (
    Dot,
    Class,
    Run,
    Option,
    Until,
    Pattern,
    Branch
)
from pe.combinators import (
    Sequence,
    Choice,
    Repeat,
)

dot = Dot()

# Numbers

digit = Class('0-9')
digits = Run(digit)

unsigned_integer = Branch('0', Pattern(Class('1-9'), digits))
integer = Pattern(Option(Class('-+')), unsigned_integer)
signed_integer = Pattern(Class('-+'), unsigned_integer)

float_fraction = Pattern('.', digits)
float_exponent = Pattern(Class('eE'), integer)
float = Pattern(integer, Option(float_fraction), Option(float_exponent))

# Strings

dqstring = Pattern('"', Until(Class('"\n'), escape='\\'), '"')
sqstring = Pattern("'", Until(Class('"\n'), escape='\\'), '"')

dq3string = Pattern('"""', Until('"""', escape='\\'), '"""')
sq3string = Pattern("'''", Until("'''", escape='\\'), "'''")


# Whitespace

Space = Class('\t\n\v\f\r ')
Spaces = Run(Space, min=1)
Spacing = Run(Space)
