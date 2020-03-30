
from typing import Dict, Callable

from pe._constants import Operator
from pe._errors import Error
from pe._definition import Definition
from pe.operators import Rule



class Grammar:
    """A parsing expression grammar definition."""

    def __init__(self,
                 definitions: Dict[str, Definition] = None,
                 actions: Dict[str, Callable] = None,
                 start: str = 'Start'):
        self.start = start
        self.definitions = definitions or {}
        self.actions = actions or {}
        self.final = False

    def __repr__(self):
        return (f'Grammar({self.definitions!r}, '
                f'actions={self.actions!r}, '
                f'start={self.start!r})')

    def __setitem__(self, name: str, definition: Definition):
        self.definitions[name] = definition

    def __getitem__(self, name):
        return self.definitions[name]

    def __eq__(self, other: object):
        if not isinstance(other, Grammar):
            return NotImplemented
        return (self.start == other.start
                and self.definitions == other.definitions
                and self.actions == other.actions)

    def finalize(self):
        if self.final:
            raise Error('grammar is already finalized')
        defs = self.definitions
        acts = self.actions
        for name in defs:
            expr = defs[name]
            if name in acts:
                if expr.op == Operator.RUL:
                    # check if name is same or None?
                    expr = expr.args[0]
                expr = Rule(expr, acts[name], name=name)
                defs[name] = expr
            _check_closed(expr, defs)
        self.final = True


def _check_closed(expr, defs):
    op = expr.op
    args = expr.args
    if op == Operator.SYM:
        if args[0] not in defs:
            raise Error(f'undefined nonterminal: {args[0]}')
    elif op in (Operator.DOT, Operator.LIT, Operator.CLS, Operator.RGX):
        pass
    elif op in (Operator.SEQ, Operator.CHC):
        for term in args[0]:
            _check_closed(term, defs)
    else:
        _check_closed(args[0], defs)
