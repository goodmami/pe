
from collections import defaultdict
import re

from pe._constants import FAIL, Operator
from pe._core import Error, Grammar


def match(grammar, s: str, pos: int = 0):
    DOT = Operator.DOT
    LIT = Operator.LIT
    CLS = Operator.CLS
    RGX = Operator.RGX
    SYM = Operator.SYM
    OPT = Operator.OPT
    RPT = Operator.RPT
    AND = Operator.AND
    NOT = Operator.NOT
    DIS = Operator.DIS
    BND = Operator.BND
    SEQ = Operator.SEQ
    CHC = Operator.CHC
    RUL = Operator.RUL

    memo = defaultdict(dict)
    agenda = [(grammar[grammar.start], pos, 0)]
    index = 0
    slen = len(s)
    while index >= 0:
        expr, start, i = agenda[index]

        op = expr.op
        exprargs = expr.args
        push = False
        print(f'pos: {pos}\tindex: {index}\texpr state: {i}\top: {op}')

        if op == RPT:
            subexpr, min, max = exprargs
            if pos == FAIL:  # item failed, ok if it matched enough
                if i >= min:
                    pos = agenda[index+1][1]  # use last successful pos
            elif i == max:  # repeat finished
                pass
            elif pos >= slen and i < min:  # end of string and not enough
                pos = FAIL
            else:
                if i == 0:  # starting
                    agenda[index+1:] = [(subexpr, pos, 0)]
                else:  # continuing; reset pos and state.i
                    agenda[index+1] = (subexpr, pos, 0)
                push = True

        elif op == SYM:
            # memoization
            # _id = id(expr)
            if pos < 0:
                pass
            # elif _id in memo[pos]:
            #     pos, push = memo[pos][_id]
            else:
                name = exprargs[0]
                if i:
                    # action = grammar.actions[name]
                    # do something
                    pass
                else:  # entering rule
                    subexpr = grammar[name]
                    agenda[index+1:] = [(subexpr, pos, 0)]
                    push = True

                # memo[pos][_id] = (pos, push)

        elif op == CHC:
            subexprs = exprargs[0]
            # starting choice or choice item failed; reset pos and try next
            if i == 0 or (pos == FAIL and i < len(subexprs)):
                pos = start
                agenda[index+1:] = [(subexprs[i], pos, 0)]
                push = True
            else:  # all choices failed or one succeeded
                pass

        elif op == SEQ:
            if pos < 0:
                pass
            else:
                subexprs = exprargs[0]
                if i >= len(subexprs):  # sequence complete
                    pass
                else:  # next sequence item
                    agenda[index+1:] = [(subexprs[i], pos, 0)]
                    push = True

        elif op == RGX:
            pattern = re.compile(exprargs[0])
            m = pattern.match(s, pos)
            if m is None:
                pos = FAIL
            else:
                pos = m.end()

        elif op == LIT:
            string = exprargs[0]
            l = len(string)
            if s[pos:pos+l] == string:
                pos += l
            else:
                pos = FAIL

        elif op == CLS:
            chars = exprargs[0]
            try:
                if s[pos] in chars:
                    pos += 1
                else:
                    pos = FAIL
            except IndexError:
                pos = FAIL

        elif op == DOT:
            try:
                s[pos]
            except IndexError:
                pos = FAIL
            else:
                pos = pos + 1

        elif op == OPT:
            if i == 0:
                agenda[index+1:] = [(exprargs[0], pos, 0)]
                push = True
            else:
                if pos == FAIL:
                    pos = start

        elif op == AND:
            if i == 0:
                agenda[index+1:] = [(exprargs[0], pos, 0)]
                push = True
            else:
                if pos != FAIL:
                    pos = start

        elif op == NOT:
            if i == 0:
                agenda[index+1:] = [(exprargs[0], pos, 0)]
                push = True
            else:
                if pos == FAIL:
                    pos = start
                else:
                    pos = FAIL

        elif op == BND:
            if i == 0:
                agenda[index+1:] = [(exprargs[1], pos, 0)]
                push = True
            else:
                if pos == FAIL:
                    pos = start
                else:
                    pos = FAIL

        elif op == DIS:
            if i == 0:
                agenda[index+1:] = [(exprargs[0], pos, 0)]
                push = True

        elif op == RUL:
            if pos < 0 or i:  # rule complete
                # action = grammar.actions[name]
                # do something
                pass
            else:  # entering rule
                subexpr = exprargs[0]
                agenda[index+1:] = [(subexpr, pos, 0)]
                push = True

        else:
            raise Error(f'invalid operation: {op!r}')

        if push:
            index += 1
        else:
            index -= 1
            old = agenda[index]
            agenda[index] = (*old[:2], old[2] + 1)

    # print(f'done\tpos: {pos}')

g = Grammar()
g.definitions['Start'] = (
    Operator.SEQ, [
        (Operator.LIT, '"'),
        (Operator.RPT, (Operator.CHC, [
            (Operator.SEQ, [(Operator.LIT, '\\'), (Operator.DOT,)]),
            (Operator.SEQ, [
                (Operator.NOT, (Operator.LIT, '"')), (Operator.DOT,)])]),
         0, -1),
        (Operator.LIT, '"')])
