
import pe
from pe.actions import pack, constant


grammar = r'''
# TOML v1.0.0-rc1
# Adapted from the ABNF at https://github.com/toml-lang/toml
#
# Some notes regarding the conversion to PEG:
#
#   * PEG literals are case-sensitive, unlike ABNF literals, so there's
#     no need to use hex escapes for simple strings
#   * Similarly, some character and character ranges are more clearly
#     expressed using PEG literal escapes or character classes
#   * ABNF literal letters need to become character classes
#   * Hyphens in nonterminal names become underscores
#   * Some rules are restructured to accommodate PEG's prioritized choice
#   * The array_values and inline_table_keyvals rules are rewritten to
#     avoid recursion errors on very large structures
#   * key and dotted_key are merged for simplicity
#   * An explicit EOF is added to make sure the whole document parses

toml <- expression ( newline expression )* EOF
EOF  <- !.

expression <- ws keyval ws comment?
            / ws table ws comment?
            / ws comment?

## Whitespace

ws     <- wschar*
wschar <- [ \t]   # Space or horizontal tab

## Newline

newline <- "\n"     # LF
         / "\r\n"   # CRLF

## Comment

comment_start_symbol <- "#"
non_ascii            <- [\x80-\uD7FF\uE000-\U0010FFFF]
non_eol              <- [\x09\x20-\x7F] / non_ascii

comment <- comment_start_symbol non_eol*

## Key-Value pairs

keyval       <- key keyval_sep val

key          <- simple_key ( dot_sep simple_key)*
simple_key   <- quoted_key / unquoted_key

unquoted_key <- ~( ALPHA / DIGIT / [-_] )+  # A-Z / a-z / 0-9 / - / _
quoted_key   <- basic_string / literal_string

dot_sep      <- ws "." ws  # . Period
keyval_sep   <- ws "=" ws  # =

val <- string / boolean / array / inline_table / date_time / float / integer

## String

string <- ml_basic_string / basic_string / ml_literal_string / literal_string

## Basic String

basic_string    <- quotation_mark ~basic_char* quotation_mark

quotation_mark  <- '"'

basic_char      <- basic_unescaped / escaped
basic_unescaped <- wschar / [\x21\x23-\x5B\x5D-\x7E] / non_ascii
escaped         <- escape escape_seq_char

escape          <- "\x5C"         # \
escape_seq_char <- "\x22"         # "    quotation mark  U+0022
                 / "\x5C"         # \    reverse solidus U+005C
                 / "b"            # b    backspace       U+0008
                 / "f"            # f    form feed       U+000C
                 / "n"            # n    line feed       U+000A
                 / "r"            # r    carriage return U+000D
                 / "t"            # t    tab             U+0009
                 / "u" HEXDIG4    # uXXXX                U+XXXX
                 / "U" HEXDIG8    # UXXXXXXXX            U+XXXXXXXX

## Multiline Basic String

ml_basic_string       <- ml_basic_string_delim ~ml_basic_body ml_basic_string_delim
ml_basic_string_delim <- quotation_mark quotation_mark quotation_mark
ml_basic_body         <- mlb_content* ( mlb_quotes mlb_content+ )* mlb_quotes?

mlb_content    <- mlb_char / newline / mlb_escaped_nl
mlb_char       <- mlb_unescaped / escaped
mlb_quotes     <- quotation_mark quotation_mark?
mlb_unescaped  <- wschar / [\x21\x23-\x5B\x5D-\x7E] / non_ascii
mlb_escaped_nl <- escape ws newline ( wschar / newline )*

## Literal String

literal_string <- apostrophe ~literal_char* apostrophe

apostrophe <- "'" # ' apostrophe

literal_char <- [\x09\x20-\x26\x28-\x7E] / non_ascii

## Multiline Literal String

ml_literal_string       <- ml_literal_string_delim ~ml_literal_body ml_literal_string_delim
ml_literal_string_delim <- apostrophe apostrophe apostrophe
ml_literal_body         <- mll_content* ( mll_quotes mll_content+ )* mll_quotes?

mll_content <- mll_char / newline
mll_char    <- [\x09\x20-\x26\x28-\x7E] / non_ascii
mll_quotes  <- apostrophe apostrophe?

## Integer

integer <- dec_int / hex_int / oct_int / bin_int

minus      <- "-"                  # -
plus       <- "+"                  # +
underscore <- "_"                  # _
digit1_9   <- [1-9]                # 1-9
digit0_7   <- [0-7]                # 0-7
digit0_1   <- [0-1]                # 0-1

hex_prefix <- "0x"                 # 0x
oct_prefix <- "0o"                 # 0o
bin_prefix <- "0b"                 # 0b

dec_int          <- ~( (minus / plus)? unsigned_dec_int )
unsigned_dec_int <- "0" / digit1_9 ( DIGIT / underscore DIGIT )*

hex_int <- hex_prefix ~( HEXDIG ( HEXDIG / underscore HEXDIG )* )
oct_int <- oct_prefix digit0_7 ( digit0_7 / underscore digit0_7 )*
bin_int <- bin_prefix digit0_1 ( digit0_1 / underscore digit0_1 )*

## Float

float <- ~( float_int_part ( exp / frac exp? )
          / special_float )

float_int_part      <- dec_int
frac                <- decimal_point zero_prefixable_int
decimal_point       <- "."
zero_prefixable_int <- DIGIT ( DIGIT / underscore DIGIT )*

exp            <- [Ee] float_exp_part
float_exp_part <- (minus / plus)? zero_prefixable_int

special_float <- (minus / plus)? ( inf / nan )
inf           <- "inf"
nan           <- "nan"

## Boolean

boolean <- true / false

true  <- "true"
false <- "false"

## Date and Time (as defined in RFC 3339)

date_time <- offset_date_time / local_date_time / local_date / local_time

date_fullyear  <- DIGIT DIGIT DIGIT DIGIT
date_month     <- DIGIT DIGIT  # 01-12
date_mday      <- DIGIT DIGIT  # 01-28, 01-29, 01-30, 01-31 based on month/year
time_delim     <- [Tt ]        # T, t, or space
time_hour      <- DIGIT DIGIT  # 00-23
time_minute    <- DIGIT DIGIT  # 00-59
time_second    <- DIGIT DIGIT  # 00-58, 00-59, 00-60 based on leap second rules
time_secfrac   <- "." DIGIT+
time_numoffset <- [-+] time_hour ":" time_minute
time_offset    <- [Zz] / time_numoffset

partial_time <- time_hour ":" time_minute ":" time_second time_secfrac?
full_date    <- date_fullyear "-" date_month "-" date_mday
full_time    <- partial_time time_offset

## Offset Date-Time

offset_date_time <- ~(full_date time_delim full_time)

## Local Date-Time

local_date_time <- ~(full_date time_delim partial_time)

## Local Date

local_date <- ~full_date

## Local Time

local_time <- ~partial_time

## Array

array <- array_open array_values? ws_comment_newline array_close

array_open  <- "["
array_close <- "]"

array_values <- ws_comment_newline val (ws array_sep ws_comment_newline val)* ws array_sep?

array_sep <- ","  # , Comma

ws_comment_newline <- ( wschar / comment? newline )*

## Table

table <- std_table / array_table

## Standard Table

std_table <- std_table_open key std_table_close

std_table_open  <- "[" ws     # [ Left square bracket
std_table_close <- ws "]"     # ] Right square bracket

## Inline Table

inline_table <- inline_table_open inline_table_keyvals? inline_table_close

inline_table_open  <- "{" ws     # {
inline_table_close <- ws "}"     # }
inline_table_sep   <- ws "," ws  # , Comma

inline_table_keyvals <- keyval (inline_table_sep keyval)*

## Array Table

array_table <- array_table_open key array_table_close

array_table_open  <- "[[" ws  # [[ Double left square bracket
array_table_close <- ws "]]"  # ]] Double right square bracket

## Built-in ABNF terms, reproduced here for clarity

ALPHA  <- [A-Za-z]
DIGIT  <- [0-9]
HEXDIG <- [0-9A-Za-z]

## Additional helper definitions

HEXDIG4 <- HEXDIG HEXDIG HEXDIG HEXDIG
HEXDIG8 <- HEXDIG4 HEXDIG4
'''


def toml_unescape(s):
    return s  # TODO


def reduce_keyval(*args):
    key, *rest = args
    if len(rest) > 1:
        return (key, reduce_keyval(*rest))
    else:
        return (key, rest[0])


actions = {
    # 'toml': pack(dict),
    'keyval': reduce_keyval,
    # 'basic_string': toml_unescape,
    # 'ml_basic_string': toml_unescape,
    'dec_int': int,
    'hex_int': lambda x: int(x, 16),
    'oct_int': lambda x: int(x, 8),
    'bin_int': lambda x: int(x, 2),
    'float': float,
    'true': constant(True),
    'false': constant(False),
    # 'offset_date_time': None,  # TODO
    # 'local_date_time': None,  # TODO
    # 'local_date': None,  # TODO
    # 'local_time': None,  # TODO
    'array': pack(list),
    # 'std_table': None,  # TODO
    'inline_table': pack(dict),
    # 'array_table': None,  # TODO
}

TOML = pe.compile(grammar, actions=actions)

if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as fh:
        m = TOML.match(fh.read())
        print(repr(m))
        if m:
            print(m.value())
