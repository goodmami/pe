
# Parsing Dates in TOML

This guide explains how one could parse date and time values in [TOML]
documents. It also serves as an example of converting an ABNF to PEG.

Here are some examples of TOML dates and times:

    1979-05-27T00:32:00-07:00  # most specific: date, time, timezone offset
    1979-05-27T07:32:00        # no timezone offset
    1979-05-27                 # date only
    07:32:00                   # "local" time only

For a full parser, see the [TOML example]; this guide
focuses on one part of it to help explain the usage of **pe**.

[TOML]: https://github.com/toml-lang/toml
[TOML example]: ../../examples/toml.py

This guide covers three main tasks:

* Inspecting the TOML specification
* Parsing the syntactic form
* Adding semantic actions to create a [datetime] object

[datetime]: https://docs.python.org/3/library/datetime.html#datetime.datetime

## Dates in the TOML Specification

TOML's [MIT-licensed][TOML-license] specification has two parts: the
descriptive specification ([toml-v1.0.0-rc.1.md] at the time of this
guide's writing), and the [ABNF] grammar ([toml.abnf]). The section
for dates and times is based on [RFC 3339], which describes a
standardized way to write dates (year, month, and day), optionally
with time with granularity down to milliseconds, and the time may
optionally have an offset to handle timezones. As TOML was designed
for configuration files and it's conceivable that a configuration file
would encode time without dates, it allows for a "local" time as well.

### date-time in the ABNF

Following is the `date-time` section of the ABNF
([link](https://github.com/toml-lang/toml/blob/0050f6fe64d82b3ba14968bf0b299a5608641165/toml.abnf#L157-L190
)):

```abnf
;; Date and Time (as defined in RFC 3339)

date-time      = offset-date-time / local-date-time / local-date / local-time

date-fullyear  = 4DIGIT
date-month     = 2DIGIT  ; 01-12
date-mday      = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on month/year
time-delim     = "T" / %x20 ; T, t, or space
time-hour      = 2DIGIT  ; 00-23
time-minute    = 2DIGIT  ; 00-59
time-second    = 2DIGIT  ; 00-58, 00-59, 00-60 based on leap second rules
time-secfrac   = "." 1*DIGIT
time-numoffset = ( "+" / "-" ) time-hour ":" time-minute
time-offset    = "Z" / time-numoffset

partial-time   = time-hour ":" time-minute ":" time-second [ time-secfrac ]
full-date      = date-fullyear "-" date-month "-" date-mday
full-time      = partial-time time-offset

;; Offset Date-Time

offset-date-time = full-date time-delim full-time

;; Local Date-Time

local-date-time = full-date time-delim partial-time

;; Local Date

local-date = full-date

;; Local Time

local-time = partial-time
```

There's quite a bit going on here, so we will take it piece by piece.


### ABNF versus PEG

First let's some of the differences between ABNF and PEG.

* literals in ABNF are case-insensitive; for case-sensitive matches,
  the character escape is used
* ABNF allows for bounded repetition, such as `4DIGIT` which means the
  `DIGIT` pattern is repeated 4 times, or `1*DIGIT` which means that
  `DIGIT` repeats one or more times
* while ultimately it depends on the parsing algorithm, alternations
  in ABNF are ambiguous, whereas PEG's are prioritized
* optionality uses `[ ... ]` in ABNF versus `( ... )?` in PEG
* rule operators are `=` versus `<-`
* comments begin with `;` versus `#`
* ABNF allows hyphens in names while PEG does not
* ABNF has some built-in terms, like `DIGIT`, which we will define
  ourselves

This list will be sufficient for our purposes.


## Parsing the Form

Now we will build a parser that only recognizes valid dates and
times. In the next section we add semantic actions to transform the
parses into interpreted values.

First import **pe** as well as the
[typing](https://docs.python.org/3/library/typing.html) module:

```python
>>> from typing import *
>>> import pe

```

To help with testing our patterns, let's define a function that sets a
start symbol and matches a grammar against some inputs. It will show
us if an input matched the grammar and, if so, what part of the input
matched.

```python
>>> def test(start: str, definitions: str, inputs: List[str]) -> None:
...     grammar = f'Start <- {start}\n{definitions}'
...     for inp in inputs:
...         m = pe.match(grammar, inp)
...         if m:
...             print(f'SUCCESS: ({m.group()}){inp[m.end:]}')
...         else:
...             print(f'FAILURE: {inp}')
...

```

### Digits

The most basic patterns to define are the digits, which are built-in
to ABNF. TOML only considers ASCII digits, so the character class
`[0-9]` is all we need. However, since standard PEG does not have
upper-bounded or exact repetition, we need to repeat the pattern
explicitly to match the two-digit and four-digit patterns. It
therefore helps to give these patterns their own definitions so they
can be reused. And finally, since [RFC 3339] dates and times use
leading zeros, we don't need to worry about single-digit numbers
(e.g., September is `09`, not `9`, etc.). This is what we get:


```python
>>> digits = r'''
...     DIGIT  <- [0-9]
...     DIGIT2 <- DIGIT DIGIT
...     DIGIT4 <- DIGIT2 DIGIT2
... '''

```

Now let's try out each pattern:

```python
>>> test('DIGIT', digits, ['', '0', '01', '0123', 'a'])
FAILURE: 
SUCCESS: (0)
SUCCESS: (0)1
SUCCESS: (0)123
FAILURE: a
>>> test('DIGIT2', digits, ['', '0', '01', '0123', 'a'])
FAILURE: 
FAILURE: 0
SUCCESS: (01)
SUCCESS: (01)23
FAILURE: a
>>> test('DIGIT4', digits, ['', '0', '01', '0123', 'a'])
FAILURE: 
FAILURE: 0
FAILURE: 01
SUCCESS: (0123)
FAILURE: a

```

Note that `DIGIT` and `DIGIT2` match not only the single- and
double-digit numbers, respectively, but also partially match any input
that starts with one or two digits. This is expected as the grammar
does not specify what comes after the matching pattern. A larger
grammar would provide the context to reject such partial matches, such
as `DIGIT2` being followed by `-` (in dates) or `:` (in times).


### Dates

With two and four digit parsing we can construct dates. Here are the relevant patterns from the ABNF:

```abnf
date-fullyear  = 4DIGIT
date-month     = 2DIGIT  ; 01-12
date-mday      = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on month/year
full-date      = date-fullyear "-" date-month "-" date-mday
```

We can rewrite it in PEG as follows:

```python
>>> date = r'''
...     date  <- year "-" month "-" day
...     year  <- DIGIT4
...     month <- DIGIT2
...     day   <- DIGIT2
... '''

```

And that's it, really. Now let's make sure it parses expected dates
and rejects unexpected ones:

```python
>>> test('date', date + digits, ['2020-04-23', '23-04-2020'])
SUCCESS: (2020-04-23)
FAILURE: 23-04-2020

```

> **Aside: Two-digit years**
>
> While it is not part of the specification (and a terrible idea in
> general), let's consider for a moment if two-digit years were
> allowed in dates as it introduces an important concept in PEG
> parsing: prioritized choice. If we altered the `date` pattern as
> follows, with the rest the same, we would introduce a grammar bug:
>
> ```python
> >>> date = r'''
> ...     date  <- (year2 / year4) "-" month "-" day
> ...     year2 <- DIGIT2
> ...     year4 <- DIGIT4
> ... '''
>
> ```
>
> The problem is that any four-digit year will begin with two digits,
> meaning that the `year2` pattern will match two- *and* four-digit
> years (recall how above `DIGIT2` partially matched the input
> `0123`). The prioritized choice in PEG means that only the first
> alternation, in order, will be used, so the `year4` pattern will
> never be attempted. The solution is to swap the order of `year2` and
> `year4`:
>
> ```python
> >>> date = r'''
> ...     date <- (year4 / year2) "-" month "-" day
> ... '''
>
> ```
>
> This way, a two-digit year will only match if `year4` failed to
> match.


### Times

Time patterns are a bit more complex because they can have optional
fractional seconds. Here are the relevant parts of the ABNF again (the
time pattern is called `partial-time` because it does not include the
time offset):

```abnf
partial-time   = time-hour ":" time-minute ":" time-second [ time-secfrac ]
time-hour      = 2DIGIT  ; 00-23
time-minute    = 2DIGIT  ; 00-59
time-second    = 2DIGIT  ; 00-58, 00-59, 00-60 based on leap second rules
time-secfrac   = "." 1*DIGIT
```

This grammar would match times such as `10:49:14` or `10:49:14.8312`.
Here is a straightforward conversion to PEG:

```python
>>> time = r'''
...     time    <- hour ":" minutes ":" seconds secfrac?
...     hour    <- DIGIT2
...     minutes <- DIGIT2
...     seconds <- DIGIT2
...     secfrac <- "." DIGIT+
... '''

```

Now we test it:

```python
>>> test('time', time + digits, ['10:49:14', '10:49:14.8312', '10:49'])
SUCCESS: (10:49:14)
SUCCESS: (10:49:14.8312)
FAILURE: 10:49

```

Note how a time without seconds is invalid for this pattern. This is
correct for the specification. Also note how there is no upper limit
to the number of fractional second digits.


### Time Offsets

The last component is a time offset. It can either be a
case-insensitive `Z`, meaning UTC time, or a positive or negative
offset of hours and minutes. Here is the ABNF:

```abnf
time-numoffset = ( "+" / "-" ) time-hour ":" time-minute
time-offset    = "Z" / time-numoffset
```

There are two alternations in these patterns, and in general we need
to be careful with alternations in PEG as they are prioritized (see
the discussion in the [Dates](#dates) section), but in this case there
are no alternations where it would matter. Also, one of these
alternations is between the two characters `+` and `-`, which in PEG
is better expressed with a character class. In addition, due to ABNF's
case insensitivity with literals, the `"Z"` needs to be expressed with
a `[Zz]` character class.

```python
>>> offset = r'''
...     offset <- [-+] hour ":" minutes
...             / [Zz]
... '''

```

> **Warning:** PEG character classes are similar to those from regular
> expressions, but they are not exactly the same. In particular, the
> second character of an `A-B` range does not need to be escaped in
> PEG, even if it is `]`. This is due to how the notation was
> originally defined, and **pe** strives to be backward compatible
> with the original notation. See [Class](../specification.md#class)
> in **pe**'s [specification](../specification.md) for more
> information. For this reason, `[+-]` is not a valid character class
> for the characters `+` and `-`. In these situations, **pe** will
> warn you about the potential problem.

Let's test the pattern against some offsets:

```python
>>> grammar = offset + time + digits
>>> test('offset', grammar, ['Z', 'z', '+02:00', '-08:00', '02:00'])
SUCCESS: (Z)
SUCCESS: (z)
SUCCESS: (+02:00)
SUCCESS: (-08:00)
FAILURE: 02:00

```

An offset without a sign is invalid, but the rest are good.


### Putting the Pieces Together

Now with the date, time, and offset components defined, we can
construct the full date-time pattern. Here are the relevant parts of
the ABNF:

```abnf
date-time        = offset-date-time / local-date-time / local-date / local-time

offset-date-time = full-date time-delim full-time
local-date-time  = full-date time-delim partial-time
local-date       = full-date
local-time       = partial-time
full-time        = partial-time time-offset
time-delim       = "T" / %x20 ; T, t, or space
```

The alternations here need to be inspected for potential ambiguity,
but it looks like they are already ordered from most to least
specific, so there is no chance of a pattern preempting a better
match. Here's a fairly straightforward translation:

```python
>>> date_time = r'''
...     date_time        <- offset_date_time / local_date_time / local_date / local_time
...     offset_date_time <- date time_delim time offset
...     local_date_time  <- date time_delim time
...     local_date       <- date
...     local_time       <- time
...     time_delim       <- [Tt ]
... '''

```

I put the `offset` pattern directly on `offset_date_time` instead of
making a separate `full_time` pattern, as this makes it more clear
what is the difference between `offset_date_time` and
`local_date_time`.

Now we can test the full grammar:

```python
>>> grammar = date_time + date + time + offset + digits
>>> test('date_time', grammar,
...      ['1979-05-27T00:32:00-07:00',
...       '1979-05-27T07:32:00',
...       '1979-05-27',
...       '07:32:00'])
SUCCESS: (1979-05-27T00:32:00-07:00)
SUCCESS: (1979-05-27T07:32:00)
SUCCESS: (1979-05-27)
SUCCESS: (07:32:00)

```

Next we will look at how to use semantic actions to construct a
[datetime] object representing a parsed date or time.


## Interpreting the Values

The parser we created above will recognize dates and times but it does
not construct any objects as it parses, not even concrete or abstract
syntax trees. We can see this by looking at the value of the match:

```python
>>> m = pe.match(grammar, '2020-04-23')
>>> print(m.group())
2020-04-23
>>> print(m.value())
None

```

> **Aside: Default start symbols**
>
> You may have noticed that I used the `grammar` string in
> `pe.match()` without encoding a start symbol as I did in the
> `test()` function. With [pe.match()](../api/pe.md#match) and
> [pe.compile()](../api/pe.md#compile), the start symbol is just the
> first definition in the grammar, regardless of what its name is.

Sometimes recognizing a string is enough, such as for producing
validators, and in those cases it can be faster to not construct any
objects. But more often you'll want the parser to actually produce
something from what it parses. When the parser produces some object as
it parses, we say it "emits" a value. There are two ways that the
parser can emit values: through captures and semantic actions.


### Captures and Actions




## Going Further: Simplifying the Grammar


```peg
date_time        <- offset_date_time / local_date_time / local_date / local_time

offset_date_time <- date time_delim time offset
local_date_time  <- date time_delim time
local_date       <- date
local_time       <- time
time_delim       <- [Tt ]

date             <- year "-" month "-" day
year             <- DIGIT4
month            <- DIGIT2
day              <- DIGIT2

time             <- hour ":" minutes ":" seconds secfrac?
hour             <- DIGIT2
minutes          <- DIGIT2
seconds          <- DIGIT2
secfrac          <- ~( "." DIGIT+ )

offset           <- [-+] hour:hour ":" minutes:minutes
                  / [Zz]

```

The named rules `date-fullyear`, `date-month`,
and `date-mday` are just meaningful names assigned to simple patterns
and are not necessary (nor are they in ABNF), although it can make the
grammar more explicit. The individual rules would be useful if a
distinct action was necessary for each component, e.g., for
validation, or if some ambiguity needed clarification (consider if the
date pattern was `DIGIT2 "-" DIGIT2 "-" DIGIT4`; is that that
`MM-DD-YYYY` or `DD-MM-YYYY`?). Another concern is legibility, and the
tradeoff here is meaningful names to quantity of rules. Since there is
no real risk of confusion and no need for custom actions (see the
[third section](#interpreting-the-values)), for brevity's sake I will
not create separate rules for these components.


```peg
date_time  <- date ( [Tt ] time (tzinfo:offset)? )?
            / time

date       <- DIGIT4 "-" DIGIT2 "-" DIGIT2
time       <- DIGIT2 ":" DIGIT2 ":" DIGIT2 time_secfrac?
secfrac    <- ~( "." DIGIT+ )
offset     <- [-+] hour:DIGIT2 ":" minutes:DIGIT2
            / [Zz]

```


[TOML-license]: https://github.com/toml-lang/toml/blob/master/LICENSE
[ABNF]: https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form
[toml.abnf]: https://github.com/toml-lang/toml/blob/master/toml.abnf
[toml-v1.0.0-rc.1.md]: https://github.com/toml-lang/toml/blob/master/versions/en/toml-v1.0.0-rc.1.md
[RFC 3339]: https://tools.ietf.org/html/rfc3339
