
# Parsing Dates in TOML

This guide explains how one could parse date and time values in [TOML]
documents. Here are some examples:

    1979-05-27T00:32:00-07:00  # most specific: date, time, timezone offset
    1979-05-27T07:32:00        # no timezone offset
    1979-05-27                 # date only
    07:32:00                   # time only

For a full parser, see the [TOML example]; this guide
focuses on one part of it to help explain the usage of **pe**.

[TOML]: https://github.com/toml-lang/toml
[TOML example]: ../../examples/toml.py

The workflow is like this:

* Inspect the TOML specification
* Parse the syntactic form
* Add semantic actions to create a [datetime] object

[datetime]: https://docs.python.org/3/library/datetime.html#datetime.datetime

## Dates in the TOML Specification

TOML's [MIT-licensed][TOML-license] specification has two parts: the
descriptive specification ([toml-v1.0.0-rc.1.md] at the time of this
guide's writing), and the [ABNF] grammar ([toml.abnf]). The section for
dates and times is based on [RFC 3339].

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
* rule operators are `=` versus `<-` in PEG
* comments begin with `;` versus `#` in PEG
* ABNF allows hyphens in names while PEG does not
* ABNF has some built-in terms, like `DIGIT`, which we will define
  ourselves in PEG

This list is sufficient for our purposes.


## Parsing the Form

Nowe we will build a parser that only recognizes valid dates and
times. In the next section we add semantic actions to transform the
parses into interpreted values.

First import **pe**:

```python
>>> import pe

```


### Digits

The most basic patterns to define are the digits, which are built-in
to ABNF. TOML only considers ASCII digits, so this makes things easy.

```peg
DIGIT  <- [0-9]
```

PEG does not have upper-bounded or exact repetition, so we can repeat
the pattern explicitly:

```peg
DIGIT2 <- DIGIT DIGIT
DIGIT4 <- DIGIT2 DIGIT2
```

Since [RFC 3339] dates and times use leading zeros, we don't need to
worry about single-digit numbers (e.g., September is `09`, not `9`,
etc.). Now let's try it out with a simple grammar:

```python
>>> digits = r'''
...     DIGIT2 <- DIGIT DIGIT
...     DIGIT4 <- DIGIT2 DIGIT2
...     DIGIT  <- [0-9]'''
>>> # define the start symbol separately so we can reuse digits
>>> start = r'Start  <- DIGIT2 / DIGIT4'
>>> for num in ('1', '12', '123', '1234'):
...     m = pe.match(start + digits, num)
...     if m:
...         print(f'matched {m.group()}')
...     else:
...         print(f'did not match {num}')
...
did not match 1
matched 12
matched 12
matched 12

```

This may not be quite what you expected. There is one main issue here,
and that is that the prioritized choice on `Start` succeeds on the
first matching alternative. Since anything that would match `DIGIT4`
will also match `DIGIT2`, `DIGIT4` should come first as it is more
precise. Let's try that again with the alternatives swapped:

```python
>>> start = r'Start  <- DIGIT4 / DIGIT2'
>>> for num in ('1', '12', '123', '1234'):
...     m = pe.match(start + digits, num)
...     if m:
...         print(f'matched {m.group()}')
...     else:
...         print(f'did not match {num}')
...
did not match 1
matched 12
matched 12
matched 1234

```

That's better. The fact that it matches `DIGIT2` against the input
`123` is not a problem (note that the `3` is not consumed); in context
a 3-digit date component would fail for other reasons, such as not
matching `-` (in dates) or `:` (in times).


### Dates

With two and four digit parsing we can construct dates. This is the
`full-date` pattern from the ABNF:

```abnf
full-date      = date-fullyear "-" date-month "-" date-mday
```

We can rewrite it in PEG as follows:

```peg
full_date <- DIGIT4 "-" DIGIT2 "-" DIGIT2
```

And that's it, really. The named rules `date-fullyear`, `date-month`,
and `date-mday` are not necessary (nor are they in ABNF), although it
can make the grammar more explicit. For brevity's sake I will not
introduce those rules here.

Now let's try it out:

```python
>>> full_date = r'''
...     full_date <- DIGIT4 "-" DIGIT2 "-" DIGIT2'''
>>> start = r'Start  <- full_date'
>>> for date in ('2020-04-23', '23-04-2020'):
...     m = pe.match(start + full_date + digits, date)
...     if m:
...         print(f'matched {m.group()}')
...     else:
...         print(f'did not match {date}')
...
matched 2020-04-23
did not match 23-04-2020

```

### The Full Grammar for Dates

```peg
date_time  <- date ( [Tt ] time (tzinfo:offset)? )?
            / time

date       <- DIGIT4 "-" DIGIT2 "-" DIGIT2

time       <- DIGIT2 ":" DIGIT2 ":" DIGIT2 time_secfrac?
secfrac   <- ~( "." DIGIT+ )

offset <- [-+] hour:DIGIT2 ":" minutes:DIGIT2
        / [Zz]

```

[TOML-license]: https://github.com/toml-lang/toml/blob/master/LICENSE
[ABNF]: https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form
[toml.abnf]: https://github.com/toml-lang/toml/blob/master/toml.abnf
[toml-v1.0.0-rc.1.md]: https://github.com/toml-lang/toml/blob/master/versions/en/toml-v1.0.0-rc.1.md
[RFC 3339]: https://tools.ietf.org/html/rfc3339
