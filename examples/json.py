
from operator import itemgetter

import pe


first = itemgetter(0)

Json = pe.compile(
    '''
    Start    <- _* (Value) _*
    Value    <- Object / Array / String / Number / Constant
    Object   <- "{" _* (Member){:COMMA} _* "}"
    Member   <- (String) _* ":" _* (Value)
    Array    <- "[" _* (Value){:COMMA} _* "]"
    String   <- '"' (?: '\\' . / !'"' . )* '"'
    Number   <- INTEGER / FLOAT
    Constant <- TRUE / FALSE / NIL
    INTEGER  <- "-"? (?: "0" / [1-9] [0-9]*)
    FLOAT    <- INTEGER FRACTION? EXPONENT?
    FRACTION <- "." [0-9]+
    EXPONENT <- [eE] [-+]? [0-9]+
    TRUE     <- "true"
    FALSE    <- "false"
    NULL     <- "null"
    COMMA    <- _* "," _*
    _        <- [\t\n\f\r ]
    ''',
    actions={
        'Start': first,
        'Object': dict,
        'Array': list,
        'String': lambda s: s[1:-1],
        'INTEGER': int,
        'FLOAT': float,
        'TRUE': lambda: True,
        'FALSE': lambda: False,
        'NULL': lambda: None,
    }
)

# # lexical patterns
# WS       = Repeat(Class('\t\n\f\r '))
# LBRACE   = Sequence('{', WS)
# RBRACE   = Sequence(WS, '}')
# LBRACKET = Sequence('[', WS)
# RBRACKET = Sequence(WS, ']')
# COLON    = Sequence(WS, ':', WS)
# COMMA    = Sequence(WS, ',', WS)
# INTEGER  = Sequence(Optional('-'), UNSIGNED_INTEGER)

# # basic values
# Integer  = Rule(INTEGER, action=int)
# Float    = Rule(FLOAT, action=float)
# String   = Rule(DQSTRING, action=lambda s: s[1:-1])
# TRUE     = Rule('true', action=lambda _: True)
# FALSE    = Rule('false', action=lambda _: False)
# NULL     = Rule('null', action=lambda _: None)

# # placeholder for recursive type
# Json     = Grammar()
# Value    = Json['Value']

# # recursive patterns
# Member   = Sequence(Group(String), COLON, Group(Value))
# Members  = Repeat(Group(Member), delimiter=COMMA)
# Object   = Rule(Sequence(LBRACE, Members, RBRACE), action=dict)

# Items    = Repeat(Group(Value), delimiter=COMMA)
# Array    = Rule(Sequence(LBRACKET, Items, RBRACKET), action=list)

# # now fill in Value
# Json['Value'] = Choice(
#     Object, Array, String, Float, Integer, TRUE, FALSE, NULL)

# Json['Start'] = Rule(Sequence(WS, Value, WS),
#                      name='Start',
#                      action=lambda xs: xs[1])

def test_numbers():
    assert Json.match('0').value() == 0
    assert Json.match('123').value() == 123
    assert Json.match('-123').value() == -123
    assert Json.match('0.5').value() == 0.5
    assert Json.match('0.5e-1').value() == 0.05
    assert Json.match('-3e+02').value() == -300.0

def test_string():
    assert Json.match('""').value() == ''
    assert Json.match('"foo"').value() == 'foo'
    assert Json.match(r'"foo\"bar"').value() == 'foo\\"bar'
    assert Json.match('"ほげ"').value() == 'ほげ'

def test_constants():
    assert Json.match('true').value() == True
    assert Json.match('false').value() == False
    assert Json.match('null').value() == None

def test_arrays():
    assert Json.match('[]').value() == []
    assert Json.match('[1]').value() == [1]
    assert Json.match('[1, 2, 3]').value() == [1, 2, 3]
    assert Json.match('[[], [], []]').value() == [[], [], []]
    assert Json.match('[[[1]]]').value() == [[[1]]]

def test_objects():
    assert Json.match('{}').value() == {}
    assert Json.match('{"key": true}').value() == {"key": True}
    assert (Json.match('{"true": true, "false": false}')
            .value() == {"true": True, "false": False})
    assert (Json.match('{"key": {"key": [1,2,3]}}')
            .value() == {'key': {'key': [1,2,3]}})
    assert (Json.match('''{
        "key": [
             1,
             2
        ]
    }''').value() == {'key': [1, 2]})


def test_recursion():
    try:
        for i in range(50,1000,10):
            Json.match(('[' * i) + (']' * i))
    except RecursionError:
        assert False, f'failed at recursion depth {i}'


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
    assert Json.match(s) is not None
    assert Json.match(s).value() == {
        'bool': [True, False],
        'number': {'float': -0.14e3, 'int': 1},
        'other': {'string': 'string', 'unicode': 'あ', 'null': None}
    }
    import timeit
    print(
        'match',
        timeit.timeit(
            'Json.match(s)',
            setup='from __main__ import Json, s',
            number=10000
        )
    )
    print(
        'scan',
        timeit.timeit(
            'Json.scan(s)',
            setup='from __main__ import Json, s',
            number=10000
        )
    )
