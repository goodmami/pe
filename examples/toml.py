
import re
import datetime

import pe
from pe.actions import Pack, Constant, Join, Capture


grammar = r'''
# TOML v1.0.0-rc1
# Adapted from the ABNF at https://github.com/toml-lang/toml
#
# Some notes regarding the conversion to PEG:
#
# * PEG literals are case-sensitive, unlike ABNF literals, so there's no
#   need to use hex escapes for simple strings
# * Similarly, some character and character ranges are more clearly
#   expressed using PEG literal escapes or character classes
# * ABNF literal letters need to become character classes
# * Hyphens in nonterminal names become underscores
# * Some rules are restructured to accommodate PEG's prioritized choice
# * The array_values and inline_table_keyvals rules are rewritten to
#   avoid recursion errors on very large structures
# * key and dotted_key are merged for simplicity
# * An explicit EOF is added to make sure the whole document parses
# * An optional newline is added to ml_basic_body for easy trimming, and
#   to ml_literal_body for the same reason
# * Multi-line strings (basic and literal) need a special rule for
#   quotes at the end of the string (e.g., x = """""foo""""")
# * date_time takes advantage of PEG's prioritized choice for simplicity

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

ml_basic_string       <- ml_basic_string_delim ml_basic_body ml_basic_string_delim
ml_basic_string_delim <- quotation_mark quotation_mark quotation_mark
ml_basic_body         <- newline? mlb_content* ( mlb_quotes mlb_content+ )* mlb_end_quotes?

mlb_content    <- ~mlb_char / ~newline / mlb_escaped_nl
mlb_char       <- mlb_unescaped / escaped
mlb_quotes     <- ~( quotation_mark quotation_mark? )
mlb_end_quotes <- ~( quotation_mark quotation_mark ) &ml_basic_string_delim
                / ~quotation_mark &ml_basic_string_delim
mlb_unescaped  <- wschar / [\x21\x23-\x5B\x5D-\x7E] / non_ascii
mlb_escaped_nl <- escape ws newline ( wschar / newline )*

## Literal String

literal_string <- apostrophe ~literal_char* apostrophe

apostrophe <- "'" # ' apostrophe

literal_char <- [\x09\x20-\x26\x28-\x7E] / non_ascii

## Multiline Literal String

ml_literal_string       <- ml_literal_string_delim ml_literal_body ml_literal_string_delim
ml_literal_string_delim <- apostrophe apostrophe apostrophe
ml_literal_body         <- newline? ~( mll_content* ( mll_quotes mll_content+ )* mll_end_quotes? )

mll_content    <- mll_char / newline
mll_char       <- [\x09\x20-\x26\x28-\x7E] / non_ascii
mll_quotes     <- apostrophe apostrophe?
mll_end_quotes <- apostrophe apostrophe &ml_literal_string_delim
                / apostrophe &ml_literal_string_delim

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

float <- float_int_part ( exp / frac exp? )
       / special_float

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

date_time          <- flexible_date_time / local_time
flexible_date_time <- full_date ( time_delim partial_time (tzinfo:time_offset)? )?
local_time         <- partial_time

date_fullyear  <- DIGIT4
date_month     <- DIGIT2  # 01-12
date_mday      <- DIGIT2  # 01-28, 01-29, 01-30, 01-31 based on month/year
time_delim     <- [Tt ]        # T, t, or space
time_hour      <- DIGIT2  # 00-23
time_minute    <- DIGIT2  # 00-59
time_second    <- DIGIT2  # 00-58, 00-59, 00-60 based on leap second rules
time_secfrac   <- ~( "." DIGIT+ )
time_numoffset <- [-+] time_hour ":" time_minute
time_offset    <- ~( [Zz] / time_numoffset )

partial_time <- time_hour ":" time_minute ":" time_second time_secfrac?
full_date    <- date_fullyear "-" date_month "-" date_mday

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

DIGIT2  <- DIGIT DIGIT
DIGIT4  <- DIGIT2 DIGIT2
HEXDIG4 <- HEXDIG HEXDIG HEXDIG HEXDIG
HEXDIG8 <- HEXDIG4 HEXDIG4
'''  # noqa: E501


class Table(tuple):
    def __repr__(self):
        return f'Table({tuple.__repr__(self)})'


class ArrayTable(tuple):
    def __repr__(self):
        return f'ArrayTable({tuple.__repr__(self)})'


def get_table(doc, path, defined):
    cur_path = ()
    cur_table = doc
    for part in path:
        cur_path += (part,)
        if defined.get(cur_path):
            raise ValueError(f'path {cur_path} already defined')
        else:
            defined[cur_path] = False
        cur_table = cur_table.setdefault(part, {})
    return cur_table, cur_path


def toml_reduce(entries):
    doc = {}  # top-level table
    defined = {}  # if key exists it's seen; if value is True it's immutable
    cur_table = doc
    cur_path = ()
    for entry in entries:

        if isinstance(entry, Table):
            if entry in defined:
                raise ValueError(f'table {tuple(entry)} already defined')
            cur_table, cur_path = get_table(doc, entry, defined)

        elif isinstance(entry, ArrayTable):
            *path, arrayname = entry
            cur_table, cur_path = get_table(doc, path, defined)
            array = cur_table.setdefault(arrayname, [])
            array.append({})
            cur_table = array[-1]
            cur_path += (arrayname,)

        else:
            key, value = entry
            table, _ = get_table(cur_table, key[:-1], defined)
            if key[-1] in defined:
                raise ValueError(f'key {cur_path + key} already defined')
            table[key[-1]] = value
            defined[cur_path + key] = True

    return doc


_toml_unesc_re = re.compile(r'\\(["\\bfnrt]|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})')
_toml_unesc_map = {
    '"': '"',
    '\\': '\\',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
}


def _toml_unescape(m):
    c = m.group(1)
    if c[0] in 'Uu':
        return chr(int(c[1:], 16))
    else:
        return _toml_unesc_map[c]


def toml_unescape(s):
    return _toml_unesc_re.sub(_toml_unescape, s)


def toml_time_offset(s):
    if s in 'Zz':
        return datetime.timezone(datetime.timedelta(0))
    else:
        hour, minutes = s.split(':')
        return datetime.timezone(
            datetime.timedelta(hours=int(hour), minutes=int(minutes)))


def toml_sec_frac(s):
    return int(float(s) * 1000)


actions = {
    'toml': Pack(toml_reduce),
    'keyval': Pack(tuple),
    'key': Pack(tuple),
    'basic_string': toml_unescape,
    'ml_basic_string': Join(toml_unescape),
    'dec_int': int,
    'hex_int': lambda x: int(x, 16),
    'oct_int': lambda x: int(x, 8),
    'bin_int': lambda x: int(x, 2),
    'float': Capture(float),
    'true': Constant(True),
    'false': Constant(False),
    'flexible_date_time': datetime.datetime,
    'local_time': datetime.time,
    'time_offset': toml_time_offset,
    'sec_frac': toml_sec_frac,
    'DIGIT2': Capture(int),
    'DIGIT4': Capture(int),
    'array': Pack(list),
    'std_table': Table,
    'inline_table': Pack(dict),
    'array_table': ArrayTable,
}

TOML = pe.compile(grammar, actions=actions, flags=pe.NONE)

if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as fh:
        m = TOML.match(fh.read())
        if m:
            print(m.value())
