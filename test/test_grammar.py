
import pe
from pe.terms import (Dot, Literal, Class)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Group,
    And,
    Not,
    # Rule,
    Grammar,
)
from pe.grammar import PEG


def test_dot():
    m = PEG['Dot'].match('.')
    assert m.value() == ('Dot',)
    m = PEG['Dot'].match('.  # comment')
    assert m.value() == ('Dot',)

def test_literal():
    expr = PEG['Literal'].match('"foo"')
    assert m.value() == ('Literal', 'foo')
    expr = PEG['Literal'].match('"foo"  # comment')
    assert m.value() == ('Literal', 'foo')
    expr = PEG['Literal'].match("'foo'")
    assert m.value() == ('Literal', 'foo')

def test_class():
    expr = PEG['Class'].match('[abc]')
    assert m.value() == ('Class', 'abc')
    expr = PEG['Class'].match('[a-c]  # comment')
    assert m.value() == ('Class', 'a-c')

def test_name():
    expr = PEG['Name'].match('abc')
    assert m.value() == ('Name', 'abc')
    expr = PEG['Name'].match('name_1  # comment')
    assert m.value() == ('Name', 'name_1')

def test_capturing_group():
    expr = PEG['Group'].match('()')
    assert m.value() == ('Group', None)
    expr = PEG['Group'].match('("a")')
    assert m.value() == ('Group', )
