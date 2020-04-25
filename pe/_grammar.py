
from typing import Dict, Callable

from pe._constants import Operator
from pe._errors import Error
from pe._definition import Definition
from pe.operators import Rule, Nonterminal


class Grammar:
    """A parsing expression grammar definition."""

    def __init__(self,
                 definitions: Dict[str, Definition] = None,
                 actions: Dict[str, Callable] = None,
                 start: str = 'Start'):
        self.definitions: Dict[str, Definition] = dict(definitions or [])
        self.actions = actions or {}
        self.start = start
        self._finalize()

    def __repr__(self):
        return (f'Grammar({self.definitions!r}, '
                f'actions={self.actions!r}, '
                f'start={self.start!r})')

    def __str__(self):
        defs = []
        width = max(len(name) for name in self.definitions)
        for name in self.definitions:
            defn = self[name].format()
            defs.append(f'{name:{width}} <- {defn}')
        return '\n'.join(defs)

    def __setitem__(self, name: str, definition: Definition):
        self.definitions[name] = definition

    def __getitem__(self, name):
        if name not in self.definitions:
            return Nonterminal(name)
        else:
            return self.definitions[name]

    def __eq__(self, other: object):
        if not isinstance(other, Grammar):
            return NotImplemented
        return (self.start == other.start
                and self.definitions == other.definitions
                and self.actions == other.actions)

    def _finalize(self):
        defs = _insert_rules(self.definitions, self.actions)
        # now recursively finalize expressions
        for expr in defs.values():
            _finalize(expr, defs, True)


def _insert_rules(defs, acts):
    for name in defs:
        expr = defs[name]
        if name in acts:
            if expr.op == Operator.RUL:
                # check if name is same or None?
                expr = expr.args[0]
            expr = Rule(expr, acts[name], name=name)
            defs[name] = expr
    return defs


def _finalize(expr, defs, structured):
    op = expr.op
    args = expr.args
    if op == Operator.SYM:
        name = args[0]
        if name not in defs:
            raise Error(f'undefined nonterminal: {args[0]}')
    elif op in (Operator.DOT, Operator.LIT, Operator.CLS, Operator.RGX):
        pass
    elif op in (Operator.SEQ, Operator.CHC):
        for term in args[0]:
            _finalize(term, defs, structured)
    elif op == Operator.CAP:
        _finalize(args[0], defs, False)
    else:
        _finalize(args[0], defs, structured)
