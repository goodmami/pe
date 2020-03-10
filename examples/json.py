
import pe
from pe.constants import Flag
from pe.actions import first, constant


Json = pe.compile(
    r'''
    Start    <- :Spacing Value
    Value    <- Object / Array / String / Number / Constant
    Object   <- :LBRACE =(Member (:COMMA Member)*)? :RBRACE
    Member   <- =(String :COLON Value)
    Array    <- :LBRACK =(Value (:COMMA Value)*)? :RBRACK
    String   <- :["] ~(!["\\] . / '\\' . )* :["] :Spacing
    Number   <- (FLOAT / INTEGER) :Spacing
    Constant <- TRUE / FALSE / NULL
    INTEGER  <- ~("-"? ("0" / [1-9] [0-9]*))
    FLOAT    <- ~(INTEGER FRACTION? EXPONENT?)
    FRACTION <- "." [0-9]+
    EXPONENT <- [eE] [-+]? [0-9]+
    TRUE     <- "true" Spacing
    FALSE    <- "false" Spacing
    NULL     <- "null" Spacing
    LBRACE   <- "{" Spacing
    RBRACE   <- "}" Spacing
    LBRACK   <- "[" Spacing
    RBRACK   <- "]" Spacing
    COMMA    <- "," Spacing
    COLON    <- ":" Spacing
    Spacing  <- [\t\n\f\r ]*
    ''',
    actions={
        'Start': first,
        'Object': dict,
        'Array': list,
        'String': str,
        'INTEGER': int,
        'FLOAT': float,
        'TRUE': constant(True),
        'FALSE': constant(False),
        'NULL': constant(None),
    },
    flags=Flag.OPTIMIZE
)


def _match(s):
    return Json.match(s, flags=Flag.STRICT).value()

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
    assert _match('true') == True
    assert _match('false') == False
    assert _match('null') == None

def test_arrays():
    assert _match('[]') == []
    assert _match('[1]') == [1]
    assert _match('[1, 2, 3]') == [1, 2, 3]
    assert _match('[0, 1.2, "string", true, false, null]'
    ) == [0, 1.2, "string", True, False, None]
    assert _match('[[], [], []]') == [[], [], []]
    assert _match('[[[1]]]') == [[[1]]]

def test_objects():
    assert _match('{}') == {}
    assert _match('{"key": true}') == {"key": True}
    assert (_match('{"true": true, "false": false}')
             == {"true": True, "false": False})
    assert (_match('{"key": {"key": [1,2,3]}}')
             == {'key': {'key': [1,2,3]}})
    assert (_match('''{
        "key": [
             1,
             2
        ]
    }''') == {'key': [1, 2]})


def test_recursion():
    i = 1
    j = 1001
    passed = True
    while True:
        try:
            _match(('[' * i) + (']' * i))
        except RecursionError:
            passed = False
            j = i
            i = int(i / 2)
            if i <= 1:
                break
        else:
            if j - i <= 1:
                break
            i += int((j - i) / 2)
    _match(('[' * i) + (']' * i))
    assert passed, f'failed at recursion depth {i}'


if __name__ == '__main__':
    s = '''{
        "bool": [
            true,
            false
        ],
        "number": {
            "float": -0.14e3,
            "int": 1
        },
        "other": {
            "string": "string",
            "unicode": "あ",
            "null": null
        }
    }'''
    assert _match(s) is not None
    assert _match(s) == {
        'bool': [True, False],
        'number': {'float': -0.14e3, 'int': 1},
        'other': {'string': 'string', 'unicode': 'あ', 'null': None}
    }
    import timeit
    print(
        'match',
        timeit.timeit(
            'match(s)',
            setup='from __main__ import Json, s; match = Json.match',
            number=10000
        )
    )
