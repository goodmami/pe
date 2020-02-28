
from pe.constants import NOMATCH, Operators as Op
from pe.core import Error
from pe.terms import (Dot, Literal, Class)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    And,
    Not,
    Grammar,
)


class State:
    __slots__ = 'expr', 'pos', 'i',
    def __init__(self, expr, pos: int):
        self.expr = expr
        self.pos = pos
        self.i = 0


def match(grammar, s: str, pos: int = 0):
    DEF = Op.DEF
    DOT = Op.DOT
    LIT = Op.LIT
    CLS = Op.CLS
    SEQ = Op.SEQ
    CHC = Op.CHC
    RPT = Op.RPT
    AND = Op.AND
    NOT = Op.NOT

    memo = {}
    agenda = [State((DEF, grammar.start), pos)]
    index = 0
    slen = len(s)
    while index >= 0:
        state = agenda[index]
        expr = state.expr
        op = expr[0]
        # print(f'pos: {pos}\tindex: {index}\tstate.i: {state.i}\top: {op}')

        if op == RPT:
            i = state.i
            subexpr, min, max = expr[1:]
            if pos == NOMATCH:  # item failed, ok if it matched enough
                if i >= min:
                    pos = agenda[index+1].pos  # use last successful pos
                index -= 1
            elif i == max:  # repeat finished
                index -= 1
            elif pos >= slen and i < min:  # end of string and not enough
                pos = NOMATCH
                index -= 1
            else:
                if i == 0:  # starting
                    agenda[index+1:] = [State(subexpr, pos)]
                else:  # continuing; reset pos and state.i
                    next_state = agenda[index+1]
                    next_state.pos = pos
                    next_state.i = 0
                index += 1
                continue

        elif op == DEF:
            if pos == NOMATCH:  # rule failed
                index -= 1
            else:
                name = expr[1]
                if state.i:  # rule complete
                    # action = grammar.actions[name]
                    index -= 1
                    # do something
                else:  # entering rule
                    subexpr = grammar[name]
                    agenda[index+1:] = [State(subexpr, pos)]
                    index += 1
                    continue

        elif op == CHC:
            i = state.i
            subexprs = expr[1]
            # starting choice or choice item failed; reset pos and try next
            if i == 0 or (pos == NOMATCH and i < len(subexprs)):
                pos = state.pos
                agenda[index+1:] = [State(subexprs[i], pos)]
                index += 1
                continue
            else:  # all choices failed or one succeeded
                index -= 1

        elif op == SEQ:
            if pos == NOMATCH:  # sequence item failed
                index -= 1
            else:
                subexprs = expr[1]
                i = state.i
                if i >= len(subexprs):  # sequence complete
                    index -= 1
                else:  # next sequence item
                    agenda[index+1:] = [State(subexprs[i], pos)]
                    index += 1
                    continue

        elif op == LIT:
            string = expr[1]
            l = len(string)
            if s[pos:pos+l] == string:
                pos += l
            else:
                pos = NOMATCH
            index -= 1

        elif op == CLS:
            chars = expr[1]
            try:
                if s[pos] in chars:
                    pos += 1
                else:
                    pos = NOMATCH
            except IndexError:
                pos = NOMATCH
            index -= 1

        elif op == DOT:
            try:
                s[pos]
            except IndexError:
                pos = NOMATCH
            else:
                pos = pos + 1
            index -= 1

        elif op == AND:
            if state.i == 0:
                agenda[index+1:] = [State(expr[1], pos)]
                index += 1
                continue
            else:
                if pos != NOMATCH:
                    pos = state.pos
                index -= 1

        elif op == NOT:
            if state.i == 0:
                agenda[index+1:] = [State(expr[1], pos)]
                index += 1
                continue
            else:
                if pos == NOMATCH:
                    pos = state.pos
                else:
                    pos = NOMATCH
                index -= 1

        else:
            raise Error(f'invalid operation: {op!r}')

        agenda[index].i += 1  # increment previous state's tally

    # print(f'done\tpos: {pos}')

class Grammar:
    def __init__(self):
        self.start = 'Start'
        self.rules = {}
        self.actions = {}
    def __getitem__(self, name):
        return self.rules[name]

g = Grammar()
g.rules['Start'] = (Op.SEQ, [(Op.LIT, '"'),
                             (Op.RPT, (Op.CHC, [
                                 (Op.SEQ, [(Op.LIT, '\\'), (Op.DOT,)]),
                                 (Op.SEQ, [(Op.NOT, (Op.LIT, '"')), (Op.DOT,)])]),
                              0, -1),
                             (Op.LIT, '"')])
