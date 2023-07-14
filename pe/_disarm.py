from pe._constants import Operator
from pe._definition import Definition


def disarm(defn: Definition) -> Definition:
    """Remove semantic effects like actions, binds, or captures."""
    op = defn.op
    if op in {Operator.RUL, Operator.BND, Operator.CAP}:
        return disarm(defn.args[0])
    elif op.type == 'Primary':
        return defn
    elif op == Operator.DBG:
        subdef = disarm(defn.args[0])
        if subdef.op == Operator.DBG:
            return subdef  # collapse debug nodes
        return Definition(op, (subdef,))
    elif op.is_unary():
        args = defn.args
        return Definition(op, (disarm(args[0]), *args[1:]))
    else:
        args = defn.args
        return Definition(
            op,
            ([disarm(arg) for arg in args[0]], *args[1:])
        )
