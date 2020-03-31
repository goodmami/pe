

import pe
from pe.actions import join, pack

X = pe.compile(
    r'''
    Start   <- Expr (EOL Expr)* EOF
    Expr    <- Term PLUS Expr
             / (Sign Sign)+ Term MINUS Expr
             / Term
    Sign    <- [-+] Spacing
    Term    <- Factor TIMES Term
             / Factor DIVIDE Term
             / Factor
    Factor  <- LPAREN Expr RPAREN
             / Atom
    Atom    <- NAME / NUMBER
    NAME    <- [a-bA-B_] [a-bA-B0-9_]* Spacing
    NUMBER  <- ('0' / [1-9] [0-9]*) Spacing
    PLUS    <- '+' Spacing
    MINUS   <- '-' Spacing
    TIMES   <- '*' Spacing
    DIVIDE  <- '/' Spacing
    LPAREN  <- '(' Spacing
    RPAREN  <- ')' Spacing
    EOL     <- '\r\n' / [\n\r]
    EOF     <- [ \t\n\v\f\r]* !.
    Spacing <- ' '*
    ''')


def _match(s):
    return X.match(s, flags=pe.STRICT|pe.MEMOIZE)


def test_x():
    assert _match('--a-b').end == 5
    assert _match('1 + 2 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + '
                  '(((((('
                  '11 * 12 * 13 * 14 * 15 + 16 * 17 + 18 * 19 * 20'
                  '))))))')
    assert _match('2*3 + 4*5*6')


if __name__ == '__main__':
    import sys
    print(0, end='')
    for i, line in enumerate(open(sys.argv[1]), 1):
        print(f'\r{i}', end='')
        X.match(line, flags=pe.STRICT|pe.MEMOIZE)
    print('done')
