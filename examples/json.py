
import pe
from pe.actions import Pack, Pair, Fail, Capture
from pe.operators import Class, Star


Json = pe.compile(
    r'''
    Start    <- Value EOF
    Value    <  Object / Array / String / Number / Constant / BADVALUE
    Object   <  "{" (Member ("," Member)*)? BADCOMMA? "}"
    Member   <  String ":" Value
    Array    <  "[" (Value ("," Value)*)? BADCOMMA? "]"
    String   <- ["] ~( (!["\\] .)* ('\\' . / (!["\\] .)+)* ) ["]
    Number   <- "-"? ("0" / [1-9] [0-9]*) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?
    Constant <- ~( "true" / "false" / "null" )
    EOF      <- !.
    BADVALUE <- ![}\]] .
    BADCOMMA <  ',' &[}\]]
    ''',
    actions={
        'Object': Pair(dict),
        'Array': Pack(list),
        'Number': Capture(float),
        'Constant': {'true': True, 'false': False, 'null': None}.__getitem__,
        'BADVALUE': Fail('unexpected JSON value'),
        'BADCOMMA': Fail('trailing commas are not allowed'),
    },
    ignore=Star(Class("\t\n\f\r ")),
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
    assert _match('{}') == _match(' { } ') == {}
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
