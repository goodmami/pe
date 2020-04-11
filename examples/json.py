
import pe
from pe.actions import first, constant, pack, fail


Json = pe.compile(
    r'''
    Start    <- Spacing Value EOF
    Value    <- Object / Array / String / Number / Constant / BADVALUE
    Object   <- LBRACE (Member (COMMA Member)*)? BADCOMMA? RBRACE
    Member   <- String COLON Value
    Array    <- LBRACK (Value (COMMA Value)*)? BADCOMMA? RBRACK
    String   <- ~( ["] (!["\\] .)* ('\\' . / (!["\\] .)+)* ["] )
    Number   <- Integer / Float
    Constant <- TRUE / FALSE / NULL
    Integer  <- ~( INTEGER ![.eE] )
    Float    <- ~( INTEGER FRACTION? EXPONENT? )
    INTEGER  <- "-"? ("0" / [1-9] [0-9]*)
    FRACTION <- "." [0-9]+
    EXPONENT <- [eE] [-+]? [0-9]+
    TRUE     <- "true"
    FALSE    <- "false"
    NULL     <- "null"
    LBRACE   <- "{" Spacing
    RBRACE   <- Spacing "}"
    LBRACK   <- "[" Spacing
    RBRACK   <- Spacing "]"
    COMMA    <- Spacing "," Spacing
    COLON    <- Spacing ":" Spacing
    Spacing  <- [\t\n\f\r ]*
    EOF      <- !.
    BADVALUE <- ![}\]] .
    BADCOMMA <- ',' &(RBRACE / RBRACK)
    ''',
    actions={
        'Start': first,
        'Object': pack(dict),
        'Member': pack(tuple),
        'Array': pack(list),
        'String': lambda s: s[1:-1],
        'Integer': int,
        'Float': float,
        'TRUE': constant(True),
        'FALSE': constant(False),
        'NULL': constant(None),
        'BADVALUE': fail('unexpected JSON value'),
        'BADCOMMA': fail('trailing commas are not allowed'),
    }
)


def _match(s):
    return Json.match(s, flags=pe.STRICT | pe.MEMOIZE).value()


def test_numbers():
    assert _match('0') == 0
    assert _match('123') == 123
    assert _match('-123') == -123
    assert _match('0.5') == 0.5
    assert _match('0.5e-1') == 0.05
    assert _match('-3e+02') == -300.0


def test_string():
    assert _match('""') == ''
    assert _match('"foo"') == 'foo'
    assert _match(r'"foo\"bar"') == 'foo\\"bar'
    assert _match('"ほげ"') == 'ほげ'


def test_constants():
    assert _match('true') is True
    assert _match('false') is False
    assert _match('null') is None


def test_arrays():
    assert _match('[]') == []
    assert _match('[1]') == [1]
    assert _match('[1, 2, 3]') == [1, 2, 3]
    assert _match(
        '[0, 1.2, "string", true, false, null]'
    ) == [0, 1.2, "string", True, False, None]
    assert _match('[[], [], []]') == [[], [], []]
    assert _match('[[[1]]]') == [[[1]]]


def test_objects():
    assert _match('{}') == {}
    assert _match('{"key": true}') == {"key": True}
    assert (_match('{"true": true, "false": false}')
            == {"true": True, "false": False})
    assert (_match('{"key": {"key": [1,2,3]}}')
            == {'key': {'key': [1, 2, 3]}})
    assert (_match('''{
        "key": [
             1,
             2
        ]
    }''') == {'key': [1, 2]})


def test_recursion():
    i = 1
    j = 1001
    while True:
        try:
            _match(('[' * i) + (']' * i))
        except RecursionError:
            j = i
            i = int(i / 2)
            if i <= 1:
                break
        else:
            if j - i <= 1:
                break
            i += int((j - i) / 2)
    _match(('[' * i) + (']' * i))
    print(f'maximum recursion depth: {i}')
    assert i > 100, f'failed at recursion depth {i}'
