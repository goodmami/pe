
from pe.constants import Operator
from pe.terms import (Dot, Literal, Class)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    And,
    Not,
    Rule,
    Grammar,
)
from pe.grammar import PEG


DEF = Operator.DEF
DOT = Operator.DOT
LIT = Operator.LIT
CLS = Operator.CLS
SEQ = Operator.SEQ
CHC = Operator.CHC
RPT = Operator.RPT
AND = Operator.AND
NOT = Operator.NOT
BND = Operator.BND


def test_dot():
    m = PEG['Dot'].match('.')
    assert m.value() == (DOT,)
    m = PEG.match('.')
    assert m.value() == (DOT,)
    m = PEG.match('.  # comment')
    assert m.value() == (DOT,)

def test_literal():
    m = PEG.match('"foo"')
    assert m.value() == (LIT, 'foo')
    m = PEG.match('"foo"  # comment')
    assert m.value() == (LIT, 'foo')
    m = PEG.match("'foo'")
    assert m.value() == (LIT, 'foo')

def test_class():
    m = PEG.match('[abc]')
    assert m.value() == (CLS, 'abc')
    m = PEG.match('[a-c]  # comment')
    assert m.value() == (CLS, 'a-c')

def test_name():
    m = PEG.match('abc')
    assert m.value() == (DEF, 'abc')
    m = PEG.match('name_1  # comment')
    assert m.value() == (DEF, 'name_1')
