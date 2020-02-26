
"""
Parsing Expression to Regular Expression conversion.
"""

import re


_special_quantifiers = {
    #min max
    (1, 1): '',
    (0, 1): '?',
    (0, -1): '*',
    (1, -1): '+',
}


# Using classname instead of isinstance is to avoid circular imports
def clsname(expr) -> str:
    """Return the class name of *expr*."""
    return expr.__class__.__name__


def set_re(expr) -> None:
    if not expr or expr._re:
        return
    name = clsname(expr)
    if name == 'Dot':
        expr._re = re.compile('.')
    elif name == 'Literal':
        expr._re = re.compile(re.escape(expr.string))
    elif name == 'Class':
        expr._re = re.compile(f'[{expr.string}]')
    elif name == 'Regex':
        expr._re = re.compile(expr.pattern, flags=expr.flags)
    elif name == 'Sequence':
        _set_sequence_re(expr)
    elif name == 'Choice':
        _set_choice_re(expr)
    elif name == 'Repeat':
        _set_repeat_re(expr)
    elif name == 'Lookahead':
        _set_lookahead_re(expr)
    elif name == 'Group':
        set_re(expr.expression)
        expr._re = expr.expression._re
    elif name == 'Rule':
        set_re(expr.expression)
        expr._re = expr.expression._re
    elif name == 'Grammar' and expr.start in expr and expr[expr.start]._re:
        expr._re = expr[expr.start]._re


def _set_sequence_re(expr):
    for e in expr.expressions:
        set_re(e)
    if all(e._re for e in expr.expressions):
        if len(expr.expressions) == 1:
            expr._re = expr.expressions[0]._re
        else:
            parts = []
            for e in expr.expressions:
                if clsname(e) == 'Choice':
                    parts.append(f'(?:{e._re.pattern})')
                else:
                    parts.append(e._re.pattern)
            expr._re = re.compile(''.join(parts))


def _set_choice_re(expr):
    for e in expr.expressions:
        set_re(e)
    if all(e._re for e in expr.expressions):
        expr._re = re.compile(
            '|'.join(e._re.pattern for e in expr.expressions))


def _quantifier_re(min, max):
    q = _special_quantifiers.get((min, max))
    if not q:
        if min == max:
            q = f'{{{max}}}'
        else:
            min = '' if min == 0 else min
            max = '' if max < 0 else max
            q = f'{{{min},{max}}}'
    return q


def _set_repeat_re(expr):
    set_re(expr.expression)

    min, max = expr.min, expr.max

    if not expr.expression._re:
        return
    if max == 0:
        expr._re = re.compile('')
        return

    pattern = expr.expression._re.pattern
    if clsname(expr.expression) in ('Sequence', 'Choice'):
        pattern = f'(?:{pattern})'

    delimiter = expr.delimiter
    set_re(delimiter)
    if delimiter and delimiter._re and max != 1:
        delim = delimiter._re.pattern
        rpt = _quantifier_re(min - 1 if min > 0 else 0,
                             -1 if max == -1 else max - 1)
        pre_re = f'{pattern}(?:{delim}{pattern}){rpt}'
        if min == 0:
            expr._re = re.compile(f'(?:{pre_re})?')
        else:
            expr._re = re.compile(pre_re)
    elif max == 1 or not delimiter:
        rpt = _quantifier_re(min, max)
        expr._re = re.compile(f'{pattern}{rpt}')


def _set_lookahead_re(expr):
    # TODO: avoid use of regex lookahead?
    set_re(expr.expression)
    _re = expr.expression._re
    if _re:
        op = '=' if expr.polarity else '!'
        expr._re = re.compile(f'(?{op}{_re.pattern})')