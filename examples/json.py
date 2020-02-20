
import timeit

import pe
from pe import (
    Class,
    Sequence,
    Choice,
    Repeat,
    Optional,
    Group,
    Grammar,
)
from pe.common import (
    UNSIGNED_INTEGER,
    FLOAT,
    DQSTRING,
)


grammar = '''
Start    <- _* Value _*
Value    <- Object | Array | String | Number | TRUE | FALSE | NIL
Object   <- "{" _* ((String) _* ":" _* (Value)){:COMMA} _* "}"
Array    <- "[" _* (Value){:COMMA} _* "]"
String   <- '"' (?: '\\' . | !'"' . )* '"'
Number   <- INTEGER | FLOAT
INTEGER  = "-"? (?: "0" | [1-9] [0-9]*)
FLOAT    = INTEGER FRACTION? EXPONENT?
FRACTION = "." [0-9]+
EXPONENT = [eE] [-+]? [0-9]+
TRUE     = "true"
FALSE    = "false"
NULL     = "null"
COMMA    = _* "," _*
_        = [\t\n\r ]
'''

WS = Repeat(Class('\t\n\f\r '))
LBRACE = Sequence('{', WS)
RBRACE = Sequence(WS, '}')
LBRACKET = Sequence('[', WS)
RBRACKET = Sequence(WS, ']')
COLON = Sequence(WS, ':', WS)
COMMA = Sequence(WS, ',', WS)

String = Group(DQSTRING, action=lambda s: s[1:-1])
Integer = Group(Sequence(Optional('-'), UNSIGNED_INTEGER), action=int)
Float = Group(FLOAT, action=float)
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

