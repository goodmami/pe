from typing import Optional

from pe._constants import Operator
from pe._definition import Definition
from pe._disarm import disarm
from pe._grammar import Grammar
from pe.operators import Sequence


def autoignore(grammar: Grammar, ignore: Optional[Definition]) -> Grammar:
    """Interleave ignore patterns around sequence items."""
    if ignore is not None:
        ignore = disarm(ignore)
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


def _autoignore(defn: Definition, ignore: Optional[Definition]) -> Definition:
    op = defn.op
    if op == Operator.IGN:
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
    elif op.type == 'Primary':
        pass
    elif op.is_unary():
        args = defn.args
        defn = Definition(op, (_autoignore(args[0], ignore), *args[1:]))
    else:
        args = defn.args
        defn = Definition(
            op,
            ([_autoignore(arg, ignore) for arg in args[0]], *args[1:])
        )
    return defn
