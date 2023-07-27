from pe._definition import Definition
from pe.operators import Bind, Capture, Literal, Rule, Sequence, Debug
from pe._disarm import disarm


def test_disarm():
    assert disarm(Capture("foo")) == Literal("foo")
    assert disarm(Bind("foo", "x")) == Literal("foo")
    assert disarm(Rule(Capture("foo"), str.upper)) == Literal("foo")
    assert (
        disarm(Sequence(Capture("foo"), Capture("bar")))
        == Sequence(Literal("foo"), Literal("bar"))
    )
    assert disarm(Debug(Capture(Debug("foo")))) == Debug(Literal("foo"))
