
from pe._constants import Operator
from pe._definition import Definition
from pe._grammar import Grammar
from pe.operators import Debug


def debug(g: Grammar):
    """Modify the grammar to report debugging information while parsing."""
    defs = g.definitions
    new = {name: _debug(defn, defs) for name, defn in defs.items()}
    return Grammar(definitions=new, start=g.start)


def _debug_terminal(defn: Definition, defs):
    return Debug(defn)


def _debug_nonterminal(defn: Definition, defs):
    return Debug(defn)


def _debug_recursive(defn: Definition, defs):
    inner = _debug(defn.args[0], defs)
    dbg_defn = Definition(defn.op, (inner,) + defn.args[1:])
    return Debug(dbg_defn)


def _debug_combining(defn: Definition, defs):
    inner = [_debug(sub, defs) for sub in defn.args[0]]
    dbg_defn = Definition(defn.op, (inner,) + defn.args[1:])
    return Debug(dbg_defn)


_op_map = {
    Operator.DOT: _debug_terminal,
    Operator.LIT: _debug_terminal,
    Operator.CLS: _debug_terminal,
    Operator.RGX: _debug_terminal,
    Operator.SYM: _debug_nonterminal,
    Operator.OPT: _debug_recursive,
    Operator.STR: _debug_recursive,
    Operator.PLS: _debug_recursive,
    Operator.AND: _debug_recursive,
    Operator.NOT: _debug_recursive,
    Operator.CAP: _debug_recursive,
    Operator.BND: _debug_recursive,
    Operator.SEQ: _debug_combining,
    Operator.CHC: _debug_combining,
    Operator.RUL: _debug_recursive,
}


def _debug(defn: Definition, defs):
    op = defn.op
    func = _op_map[op]
    return func(defn, defs)
