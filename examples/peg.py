
import pe


peg_acceptor = pe.compile(
    r'''
    # Hierarchical syntax
    Grammar    <- Spacing Definition+ EndOfFile
    Definition <- Identifier LEFTARROW Expression
    Expression <- Sequence (SLASH Sequence)*
    Sequence   <- Prefix*
    Prefix     <- (AND / NOT)? Suffix
    Suffix     <- Primary (QUESTION / STAR / PLUS)?
    Primary    <- Identifier !LEFTARROW
                / OPEN Expression CLOSE
                / Literal
                / Class
                / DOT

    # Lexical syntax
    Identifier <- IdentStart IdentCont* Spacing
    IdentStart <- [a-zA-Z_]
    IdentCont  <- IdentStart / [0-9]

    Literal    <- ['] (!['] Char)* ['] Spacing
                / ["] (!["] Char)* ["] Spacing
    Class      <- '[' (!']' Range)* ']' Spacing
    Range      <- Char '-' Char / Char
    Char       <- '\\' [nrt'"\[\]\\]
                / '\\' [0-2] [0-7] [0-7]
                / '\\' [0-7] [0-7]?
                / !'\\' .

    LEFTARROW  <- '<-' Spacing
    SLASH      <- '/' Spacing
    AND        <- '&' Spacing
    NOT        <- '!' Spacing
    QUESTION   <- '?' Spacing
    STAR       <- '*' Spacing
    PLUS       <- '+' Spacing
    OPEN       <- '(' Spacing
    CLOSE      <- ')' Spacing
    DOT        <- '.' Spacing

    Spacing    <- (Space / Comment)*
    Comment    <- '#' (!EndOfLine .)* EndOfLine
    Space      <- ' ' / '\t' / EndOfLine
    EndOfLine  <- '\r\n' / '\n' / '\r'
    EndOfFile  <- !.
    ''')

def test_accept():
    assert peg_acceptor.match('A <- "a"')
    assert peg_acceptor.match('A <- B   B <- "b"')
    assert not peg_acceptor.match('"c"')
    assert not peg_acceptor.match('A <- `c`')
