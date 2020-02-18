
import timeit

import pe
from pe import (
    Class,
    Pattern,
    Option,
    Run,
    Sequence,
    Choice,
    Repeat,
    Group,
    Grammar,
)
from pe.common import (
    unsigned_integer,
    float as float_scanner,
    dqstring,
)


grammar = '''
Start    = _* Value _*
Value    = Object | Array | String | Number | "true" | "false" | "nil"
Object   = "{" _* ((String) _* ":" _* (Value)){:COMMA} _* "}"
Array    = "[" _* vals=(Value){:COMMA} _* "]"
String   = '"' ('\\' . | !'"' .)* '"'
Number   = Integer | Float
Integer  = "-"? (?: "0" | [1-9] [0-9]*)
Float    = Integer Fraction? Exponent?
Fraction = "." [0-9]+
Exponent = [eE] [-+]? [0-9]+
TRUE     = "true"
FALSE    = "false"
NULL     = "null"
COMMA    = _* "," _*
_        = [\t\n\r ]
'''

WS = Run(Class('\t\n\f\r '))
LBRACE = Pattern('{', WS)
RBRACE = Pattern(WS, '}')
LBRACKET = Pattern('[', WS)
RBRACKET = Pattern(WS, ']')
COLON = Pattern(WS, ':', WS)
COMMA = Pattern(WS, ',', WS)

String = Group(dqstring, action=lambda s: s[1:-1])
Integer = Group(Pattern(Option('-'), unsigned_integer), action=int)
Float = Group(float_scanner, action=float)
TRUE = Group('true', action=lambda _: True)
FALSE = Group('false', action=lambda _: False)
NULL = Group('null', action=lambda _: None)

g = Grammar()
g['Start'] = Sequence(WS, g.lookup('Value'), WS)
g['Object'] = Group(
    Sequence(
        LBRACE,
        Repeat(Group(Sequence(String, COLON, g.lookup('Value'))),
               delimiter=COMMA),
        RBRACE),
    action=dict)
g['Array'] = Group(
    Sequence(
        LBRACKET,
        Repeat(g.lookup('Value'), delimiter=COMMA),
        RBRACKET),
    action=list)
g['Value'] = Choice(g.lookup('Object'),
                    g.lookup('Array'),
                    String,
                    Integer,
                    Float,
                    TRUE,
                    FALSE,
                    NULL)

m = g.match('-123456')
print(m)
print(repr(m.value()))
assert m.value() == -123456

# actions = {
#     'Object': dict,
#     'Array': list,
#     'Integer': int,
#     'Float': float,
#     'String': lambda s: s[1:-1]
# }

# parser = pe.compile(grammar, actions=actions, constants=constants)

# assert parser('-123456') == -123456

# print(timeit.timeit('parser.parse("-123456")',
#                     setup='from __main__ import parser'))

