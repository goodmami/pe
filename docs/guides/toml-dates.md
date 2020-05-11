
# Parsing Dates in TOML

This guide explains how one could parse date and time values in [TOML]
documents. It also serves as an example of converting an ABNF to PEG.

Here are some examples of TOML dates and times:

    1979-05-27T00:32:00-07:00  # most specific: date, time, timezone offset
    1979-05-27T07:32:00        # no timezone offset
    1979-05-27                 # date only
    07:32:00                   # "local" time only

For a full parser, see the [TOML example]; this guide focuses on one
part of it to help explain the usage of **pe**.

This guide covers the following tasks:

* [Inspecting the TOML specification](#dates-in-the-toml-specification)
* [Parsing the syntactic form](#parsing-the-form)
* [Adding semantic actions to create a datetime object](#interpreting-the-values)
* [Going Further: Simplifying the Grammar](#going-further-simplifying-the-grammar)


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
([link][TOML-ABNF]). Look it over to get just a basic idea of how it
parses the dates shown above:

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

First import **pe**:

```python-console
>>> import pe

```

To help with testing our patterns, let's define a function that sets a
start symbol and matches a grammar against some inputs. It will show
us if an input matched the grammar and, if so, what part of the input
matched.

```python-console
>>> def test(start, definitions, inputs):
...     grammar = f'Start <- {start}\n{definitions}'
...     for inp in inputs:
...         m = pe.match(grammar, inp)
...         if m:
...             print(f'SUCCESS: ({m.group()}){inp[m.end():]}')
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


```python-console
>>> digits = r'''
...     DIGIT  <- [0-9]
...     DIGIT2 <- DIGIT DIGIT
...     DIGIT4 <- DIGIT2 DIGIT2
... '''

```

Now let's try out each pattern:

```python-console
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

With two and four digit parsing we can construct dates. Here are the
relevant patterns from the ABNF:

```abnf
date-fullyear  = 4DIGIT
date-month     = 2DIGIT  ; 01-12
date-mday      = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on month/year
full-date      = date-fullyear "-" date-month "-" date-mday
```

We can rewrite it in PEG as follows:

```python-console
>>> date = r'''
...     date  <- year "-" month "-" day
...     year  <- DIGIT4
...     month <- DIGIT2
...     day   <- DIGIT2
... '''

```

And that's it, really. Now let's make sure it parses expected dates
and rejects unexpected ones:

```python-console
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
> ```python-console
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
> ```python-console
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

```python-console
>>> time = r'''
...     time    <- hour ":" minute ":" second secfrac?
...     hour    <- DIGIT2
...     minute  <- DIGIT2
...     second  <- DIGIT2
...     secfrac <- "." DIGIT+
... '''

```

Now we test it:

```python-console
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

```python-console
>>> offset = r'''
...     offset <- [-+] hour ":" minute
...             / [Zz]
... '''

```

> **Warning:** PEG character classes are similar to those from regular
> expressions, but they are not exactly the same. In particular, the
> second character of an `A-B` range does not need to be escaped in
> PEG, even if it is `]`. This is due to how the notation was
> originally defined, and **pe** strives to be backward compatible
> with the original notation. See [Class] in **pe**'s [specification]
> for more information. For this reason, `[+-]` is not a valid
> character class for the characters `+` and `-`. In these situations,
> **pe** will warn you about the potential problem.

Let's test the pattern against some offsets:

```python-console
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

```python-console
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

```python-console
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

Next we will look at how to use semantic actions to construct
[datetime] objects representing a parsed date or time.


## Interpreting the Values

The parser we created above will recognize dates and times but it does
not construct any objects as it parses, not even concrete or abstract
syntax trees. We can see this by looking at the value of the match:

```python-console
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
> `test()` function. With [pe.match()] and [pe.compile()], the start
> symbol is just the first definition in the grammar, regardless of
> what its name is.

Sometimes recognizing a string is enough, such as for simple format
validators, and in those cases it can be faster to not construct any
objects. But more often you'll want the parser to actually produce
something from what it parses. When the parser produces some object as
it parses, we say it "emits" a value. There are two ways that the
parser can emit values: through captures and semantic actions.


### Captures and Actions

Captures are special expressions that take the substring matched by a
subexpression and emit it. Actions transform emitted values, e.g., for
converting a captured string into an integer or for grouping multiple
values into a list. Actions can also work if there are no emitted
values, such as for returning constant values.

What we want to do is transform the parsed components of a date into
[datetime] objects. Let's start by looking at ways to construct these
objects. Once we match the full string, we could pass it to
[datetime.fromisoformat], but there are some downsides: (a) it
requires Python 3.7, which is not the minimum version needed by
**pe**; (b) it wouldn't work for times without dates; and (c) it means
that some other code needs to parse the string again, which is neither
efficient nor satisfying. Instead let's look at how to instantiate a
[datetime.datetime] object directly:

```python
datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0)
```

Since we are already parsing those components separately, we can pass
them along to these parameters, but first we need to capture and
convert these values. Since they all use the `DIGIT2` or `DIGIT4`
definitions, we can capture at that point:

```python-console
>>> digits = r'''
...     DIGIT  <- [0-9]
...     DIGIT2 <- ~( DIGIT DIGIT )
...     DIGIT4 <- ~( DIGIT2 DIGIT2 )
... '''

```

And let's see what happens:

```python-console
>>> grammar = date_time + date + time + offset + digits
>>> m = pe.match(grammar, '2020-04-23')
>>> print(m.group())
2020-04-23
>>> print(m.value())
2020

```

But why is only `'2020'` returned? The [Match.value()] method returns
the [determined value], which is only the first emitted value or
`None` if there are no emitted values (as shown earlier). This might
be confusing at first but it's actually quite useful. The other values
are still there and they're accessible with the [Match.groups()]
method:

```python-console
>>> print(m.groups())
('2020', '04', '23')

```

The other place that uses the *determined value* is when binding a
value to a name (i.e., a named capture). Actions, however, use all
emitted and bound values, and we will use that to our
advantage. Actions are assigned on the [pe.compile()] or [pe.match()]
functions' `actions` parameter. For example, we can convert the
matched substrings to integers as follows:

```python-console
>>> actions = {'DIGIT2': int, 'DIGIT4': int}
>>> m = pe.match(grammar, '2020-04-23', actions=actions)
>>> print(m.groups())
(2020, 4, 23)

```

> **Aside: Capture expressions versus Capture actions**
>
> If your primary purpose for using a capture expression (e.g.,
> `~[0-9]+`) is to apply some operation on it such as numeric
> conversion, you might consider the [Capture] action. Using a capture
> expression and a separate action achieves the same end, but it takes
> two operations to achieve that end instead of one. If you want to
> keep the string value, or you are not capturing the entire defined
> expression (i.e., some part will be ignored), stick with capture
> expressions. Here's an example of using the [Capture] action:
>
> ```python-console
> >>> from pe.actions import Capture
> >>> m = pe.match(r'DIGITS <- [0-9]+',
> ...              '123',
> ...              actions={'DIGITS': Capture(int)})
> >>> m.value()
> 123
>
> ```
>
> For this guide, however, I will stick with using capture
> expressions and simple actions.

### Constructing `datetime` Objects

In order to get our integer values into [datetime] objects, we will
exploit the fact that the positional parameters of [datetime.datetime]
are in the same order as our date formats. All we have to do is assign
[datetime.datetime] as the action. Here I will use [pe.compile()] to
streamline things a bit.

```python-console
>>> import datetime
>>> actions.update(
...     offset_date_time=datetime.datetime,
...     local_date_time=datetime.datetime,
...     local_date=datetime.datetime)
>>> parser = pe.compile(grammar, actions=actions)

```

Then we can test it with the parser's `match()` method:

```python-console
>>> parser.match('2020-04-23').value()
datetime.datetime(2020, 4, 23, 0, 0)
>>> parser.match('2020-04-23T10:28:08').value()
datetime.datetime(2020, 4, 23, 10, 28, 8)
>>> parser.match('2020-04-23T10:28:08.134').value()
datetime.datetime(2020, 4, 23, 10, 28, 8)
>>> parser.match('2020-04-23T10:28:08Z').value()
datetime.datetime(2020, 4, 23, 10, 28, 8)
>>> parser.match('2020-04-23T10:28:08-07:00').value()
Traceback (most recent call last):
  ...
TypeError: tzinfo argument must be None or of a tzinfo subclass, not type 'int'

```

This is pretty close, but there are two things left to do for these
objects: (1) fractional seconds, and (2) time offsets.

#### Fractional Seconds

The `secfrac` definition does not use `DIGIT2` nor `DIGIT4`, so it
does not get the captured and converted integer value. While the
[datetime] objects take a `microsecond` integer argument, casting
`secfrac`'s digits directly to an integer as with `DIGIT2` and
`DIGIT4` would be a mistake, as leading zeros would be ignored (`.01`
and `.1` would yield the same integer). Instead we can write a custom
function that casts the match as a float, then convert that to
microseconds. But first we need to capture the `secfrac` match. Here's
how that could be done:

```python-console
>>> time = r'''
...     time    <- hour ":" minute ":" second secfrac?
...     hour    <- DIGIT2
...     minute  <- DIGIT2
...     second  <- DIGIT2
...     secfrac <- ~( "." DIGIT+ )  # capture full expression
... '''
>>> grammar = date_time + date + time + offset + digits
>>> def secfrac_to_int(s: str) -> int:
...     return int(float(s) * 1_000_000)
...
>>> actions.update(secfrac=secfrac_to_int)
>>> parser = pe.compile(grammar, actions=actions)
>>> parser.match('2020-04-23T10:28:08.134').value()
datetime.datetime(2020, 4, 23, 10, 28, 8, 134000)

```

#### Time Offsets

Constructing time offsets is more complicated. Firstly, if you get an
offset but no microsecond value, the positional arguments will not be
used correctly (the offset will be used as the microsecond
value). This is an easy fix with **pe**'s binding expressions. We will
change the `offset_date_time` definition in the grammar as follows:

```python-console
>>> date_time = r'''
...     date_time        <- offset_date_time / local_date_time / local_date / local_time
...     offset_date_time <- date time_delim time tzinfo:offset  # bind offset to tzinfo name
...     local_date_time  <- date time_delim time
...     local_date       <- date
...     local_time       <- time
...     time_delim       <- [Tt ]
... '''

```

Now the offset, if present, will always be passed as the `tzinfo`
parameter. If it's not present, the `tzinfo` parameter is not set and
uses the default value.

Next we need to construct the appropriate object when an offset is
given. The [datetime] documentation describes [datetime.tzinfo] as an
abstract base class for which you define your own subclasses for
particular timezones, or you can use the generic [datetime.timezone]
class. Since we are not working with one particular timezone, the
[datetime.timezone] class will work. It is created with the following
signature

```python
datetime.timezone(offset, name=None)
```

The *offset* argument is a [datetime.timedelta] object, which is
created with the following signature:

```python
datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
```

As you can see, with only hour and minute values we cannot simply use
[datetime.timedelta] as the action because the positional arguments would not line up (as with [datetime.datetime] above). Unfortunately, binding expression do not work here for two reasons:

1. They will not handle negative offsets properly
2. They don't help us wrap the [datetime.timedelta] with a [datetime.timezone] object

So in this case it makes sense to write a function. We could make it
work with only [datetime] classes as actions by restructuring the
grammar, but it would be neither intuitive nor efficient. Here is a
function that does what we want, but we still need to modify the
grammar in order to capture the offset's sign and to separate the two
alternative patterns so we can assign separate actions.

```python-console
>>> def delta_to_tzinfo(sign: str, hours: int, minutes: int) -> datetime.tzinfo:
...     delta = datetime.timedelta(hours=hours, minutes=minutes)
...     if sign == '-':
...         delta *= -1
...     return datetime.timezone(delta)
...
>>> offset = r'''
...     offset <- delta / utc
...     delta  <- ~[-+] hour ":" minute
...     utc    <- [Zz]
... '''
>>> from pe.actions import Constant
>>> grammar = date_time + date + time + offset + digits
>>> actions.update(delta=delta_to_tzinfo, utc=Constant(datetime.timezone.utc))
>>> parser = pe.compile(grammar, actions=actions)
>>> parser.match('2020-04-23T10:28:08Z').value().tzinfo.tzname(None)
'UTC'
>>> parser.match('2020-04-23T10:28:08-07:00').value().tzinfo.tzname(None)
'UTC-07:00'

```

There is probably some way to combine the `utc` and `delta` patterns
so they use the same action (noting that calling [datetime.timedelta]
with no arguments is a delta of 0, the same as UTC), but it might
obfuscate the grammar a bit, so it's probably not worth it.


### Constructing `time` Objects

Finally we need to construct [datetime.time] objects for inputs that
do not include a date. By now this should seem obvious, and besides
we've already dealt with times inside of [datetime.datetime]
objects. All we need is an action:

```python-console
>>> actions.update(local_time=datetime.time)
>>> parser = pe.compile(grammar, actions=actions)
>>> parser.match('07:41:00').value()
datetime.time(7, 41)
>>> parser.match('07:41:13.0867').value()
datetime.time(7, 41, 13, 86700)

```

## Going Further: Simplifying the Grammar

Now we have a complete parser for TOML-style dates and times. Here is
the full grammar:

```peg
date_time        <- offset_date_time / local_date_time / local_date / local_time

offset_date_time <- date time_delim time tzinfo:offset
local_date_time  <- date time_delim time
local_date       <- date
local_time       <- time
time_delim       <- [Tt ]

date             <- year "-" month "-" day
year             <- DIGIT4
month            <- DIGIT2
day              <- DIGIT2

time             <- hour ":" minute ":" second secfrac?
hour             <- DIGIT2
minute           <- DIGIT2
second           <- DIGIT2
secfrac          <- ~( "." DIGIT+ )

offset           <- delta / utc
delta            <- ~[-+] hour ":" minute
utc              <- [Zz]

```

It's not too complicated, but it could be even simpler. The named
rules `year`, `month`, `day`, `hour`, `minute`, and `second` are just
meaningful names assigned to simple patterns and are not necessary
(nor are their counterparts in ABNF), although it can make the grammar
more explicit. The individual rules would be useful if a distinct
action was necessary for each component, e.g., for validation, or if
some ambiguity needed clarification (consider if the date pattern was
`DIGIT2 "-" DIGIT2 "-" DIGIT4`; is that that `MM-DD-YYYY` or
`DD-MM-YYYY`?). Another concern is legibility, and the tradeoff here
is meaningful names to quantity of rules. Since there is no real risk
of confusion and no need for custom actions (see the [third
section](#interpreting-the-values)), for brevity's sake we can inline
these definitions.

Also, if you take a look at the three date patterns, you'll see that
`offset_date_time` is just `local_date_time` with an offset, and
`local_date_time` is just `local_date` with a time. These can be
easily expressed as a single expression. Here is the revised grammar:

```peg
date_time        <- offset_date_time / local_time
offset_date_time <- date ( [Tt ] time (tzinfo:offset)? )?
local_time       <- time

date             <- DIGIT4 "-" DIGIT2 "-" DIGIT2
time             <- DIGIT2 ":" DIGIT2 ":" DIGIT2 time_secfrac?
secfrac          <- ~( "." DIGIT+ )
offset           <- delta / utc
delta            <- ~[-+] DIGIT2 ":" DIGIT2
utc              <- [Zz]

```


[pe.match()]: ../api/pe.md#match
[pe.compile()]: ../api/pe.md#compile
[Match.value()]: ../api/pe.md#Match-value
[Match.groups()]: ../api/pe.md#Match-groups
[Match.groups()]: ../api/pe.actions.md#Capture
[specification]: ../specification.md
[determined value]: ../specification.md#value-determination
[Class]: ../specification.md#class
[TOML example]: ../../examples/toml.py

[TOML]: https://github.com/toml-lang/toml
[TOML-license]: https://github.com/toml-lang/toml/blob/master/LICENSE
[TOML-ABNF]: https://github.com/toml-lang/toml/blob/0050f6fe64d82b3ba14968bf0b299a5608641165/toml.abnf#L157-L190
[toml-v1.0.0-rc.1.md]: https://github.com/toml-lang/toml/blob/master/versions/en/toml-v1.0.0-rc.1.md
[toml.abnf]: https://github.com/toml-lang/toml/blob/master/toml.abnf

[datetime]: https://docs.python.org/3/library/datetime.html
[datetime.datetime]: https://docs.python.org/3/library/datetime.html#datetime.datetime
[datetime.time]: https://docs.python.org/3/library/datetime.html#datetime.time
[datetime.fromisoformat]: https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat
[datetime.tzinfo]: https://docs.python.org/3/library/datetime.html#datetime.tzinfo
[datetime.timezone]: https://docs.python.org/3/library/datetime.html#datetime.timezone
[datetime.timedelta]: https://docs.python.org/3/library/datetime.html#datetime.timedelta

[ABNF]: https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form
[RFC 3339]: https://tools.ietf.org/html/rfc3339
