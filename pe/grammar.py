
"""Self-hosted parser for pe's grammar format."""

from pe import (
    Class,
    Sequence,
    Choice,
    Repeat,
    Optional,
    Group,
    Ahead,
    NotAhead,
    Rule,
    Grammar,
)

G = Grammar()

_DOT = Dot()
G['EndOfFile']  = NotAhead(Dot())
G['EndOfLine']  = Choice(r'\r\n', r'\r', r'\n')
_RestOfLine = Repeat(Sequence(NotAhead(G['EndOfLine']), _DOT))
G['Comment']    = Sequence('#', _RestOfLine, G['EndOfLine'])
G['Space']      = Choice(' ', r'\t', G['EndOfLine'])
G['Spacing']    = Repeat(Choice(G['Space'], G['Comment']))

G['LEFTARROW']  = Sequence('<-', G['Spacing'])
G['SLASH']      = Sequence('/', G['Spacing'])
G['AND']        = Sequence('&', G['Spacing'])
G['NOT']        = Sequence('!', G['Spacing'])
G['QUESTION']   = Sequence('?', G['Spacing'])
G['STAR']       = Sequence('*', G['Spacing'])
G['PLUS']       = Sequence('+', G['Spacing'])
_GroupType = Optional(Sequence('?', _DOT))
G['OPEN']       = Sequence('(', Group(_GroupType), G['Spacing'])
G['CLOSE']      = Sequence(')', G['Spacing'])
G['DOT']        = Sequence('.', G['Spacing'])

G['Char']       = Choice(
    Sequence('\\', Class(r'nrt\'"\[\]\\')),
    Sequence('\\', Class('0-2'), Class('0-7'), Class('0-7')),
    Sequence('\\', Class('0-7'), Optional(Class('0-7'))),
    Sequence(NotAhead('\\'), _DOT))
G['Range']      = Choice(
    Sequence(G['Char'], '-', G['Char']),
    G['Char'])

G['Class']      = Rule(
    Sequence('[', Repeat(Class(r'^\]\\'), escape=_ESC), ']'),
    action=lambda s: Class(s[1:-1]))

_ESC = Sequence('\\', _DOT)
G['Literal']    = Rule(
    Choice(Sequence("'", Repeat(Class(r"^'\\"), escape=_ESC), "'"),
           Sequence("'", Repeat(Class(r'^"\\'), escape=_ESC), '"')),
           action=lambda s: Literal(s[1:-1]))

G['IdentStart'] = Class('a-zA-Z_')
G['IdentCont']  = Choice(G['IdentStart'], Class('0-9'))
G['Identifier'] = Sequence(
    G['IdentStart'], Repeat(G['IdentCont']), G['Spacing'])

G['RuleName']   = Rule(
    Sequence(G['Identifier'], NotAhead(G['LEFTARROW'])),
    action=lambda s: ('Name', s))
G['Group']      = Rule(
    Sequence(G['OPEN'], Group(G['Expression']), G['CLOSE']),
    action=lambda xs: ('Group', *xs))
G['Term']       = Rule(Choice(G['Literal'], G['Class']),
                       action=lambda t: ('Term', t))
G['Primary']    = Choice(G['RuleName'], G['Group'], G['Term'])

G['Suffix']     = Sequence(
    G['Primary'], Optional(Choice(G['QUESTION'], G['STAR'], G['PLUS'])))
G['Prefix']     = Sequence(
    Optional(Choice(G['AND'], G['NOT'])), G['Suffix'])
G['Sequence']   = Repeat(G['Prefix'])
G['Expression'] = Repeat(G['Sequence'], delimiter=G['SLASH'])

G['Definition'] = Sequence(G['Identifier'], G['LEFTARROW'], G['Expression'])
G['Grammar']    = Sequence(
    G['Spacing'], Repeat(G['Definition'], min=1), G['EndOfFile'])
