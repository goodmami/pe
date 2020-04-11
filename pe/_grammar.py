
from typing import Dict, Callable

from pe._constants import Operator, Value
from pe._errors import Error, GrammarError
from pe._definition import Definition
from pe.operators import Rule, Nonterminal


class Grammar:
    """A parsing expression grammar definition."""

    def __init__(self,
                 definitions: Dict[str, Definition] = None,
                 actions: Dict[str, Callable] = None,
                 start: str = 'Start'):
        self.start = start
        self.definitions: Dict[str, Definition] = dict(definitions or [])
        self.actions = actions or {}
        self.final = False

    def __repr__(self):
        return (f'Grammar({self.definitions!r}, '
                f'actions={self.actions!r}, '
                f'start={self.start!r})')

    def __str__(self):
        defs = []
        width = max(len(name) for name in self.definitions)
        for name in self.definitions:
            defn = self[name].format(len(name) + 2)
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

    def finalize(self):
        if self.final:
            raise Error('grammar is already finalized')
        defs = _insert_rules(self.definitions, self.actions)
        _resolve_deferred(defs)
        # now recursively finalize expressions
        for expr in defs.values():
            _finalize(expr, defs, True)
        self.final = True


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


def _resolve_deferred(defs):
    resolved = {}
    for name, expr in defs.items():
        if expr.value != Value.DEFERRED:
            resolved[name] = expr.value
    to_resolve = set(defs).difference(resolved)
    while to_resolve:
        found = False
        for name in to_resolve:
            expr = defs[name]
            op = expr.op
            inner = expr.args[0]
            if op == Operator.SYM and inner in resolved:
                resolved[name] = resolved[expr.args[0]]
            elif op == Operator.RUL and inner.value != Value.DEFERRED:
                resolved[name] = inner.value
            if name in resolved:
                expr.value = resolved[name]
                to_resolve.remove(name)
                found = True
                break
        if not found:
            raise GrammarError('could not resolve expressions: {}'
                               .format(', '.join(to_resolve)))


def _finalize(expr, defs, structured):
    op = expr.op
    args = expr.args
    if not structured:
        expr.value = Value.EMPTY
    if op == Operator.SYM:
        name = args[0]
        if name not in defs:
            raise Error(f'undefined nonterminal: {args[0]}')
        expr.value = defs[name].value
    elif op in (Operator.DOT, Operator.LIT, Operator.CLS, Operator.RGX):
        pass
    elif op in (Operator.SEQ, Operator.CHC):
        for term in args[0]:
            _finalize(term, defs, structured)
    elif op == Operator.RAW:
        _finalize(args[0], defs, False)
    else:
        _finalize(args[0], defs, structured)
