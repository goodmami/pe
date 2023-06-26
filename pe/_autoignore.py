from typing import Optional

from pe._constants import Operator
from pe._definition import Definition
from pe._grammar import Grammar
from pe.operators import Sequence


def autoignore(grammar: Grammar, ignore: Optional[Definition]) -> Grammar:
    """Interleave ignore patterns around sequence items."""
    new = {
        name: _autoignore(defn, ignore)
        for name, defn
        in grammar.definitions.items()
    }
    return Grammar(
        definitions=new,
        actions=grammar.actions,
        start=grammar.start
    )


_single_expr_ops = {
    Operator.OPT,
    Operator.STR,
    Operator.PLS,
    Operator.AND,
    Operator.NOT,
    Operator.CAP,
    Operator.BND,
    Operator.RUL,
    Operator.DEF,
}

_multi_expr_ops = {
    Operator.SEQ,
    Operator.CHC,
}


def _autoignore(defn: Definition, ignore: Optional[Definition]) -> Definition:
    if defn.op == Operator.IGN:
        subdef = _autoignore(defn.args[0], ignore)
        if ignore is not None:
            if subdef.op == Operator.SEQ:
                items = [ignore]
                for item in subdef.args[0]:
                    items.append(item)
                    items.append(ignore)
            else:
                items = [ignore, subdef, ignore]
            subdef = Sequence(*items)
        defn = subdef
    elif defn.op in _single_expr_ops:
        args = defn.args
        defn = Definition(defn.op, (_autoignore(args[0], ignore), *args[1:]))
    elif defn.op in _multi_expr_ops:
        args = defn.args
        defn = Definition(
            defn.op,
            ([_autoignore(arg, ignore) for arg in args[0]], *args[1:])
        )
    # do nothing for primary expressions
    return defn
