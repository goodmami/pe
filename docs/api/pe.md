
# API Reference: pe

## Functions

pe.**<a id="compile" href="#compile">compile</a>**
(*source, actions=None, parser='packrat', flags=pe.NONE*)

Compile the parsing expression or grammar defined in *source* and
return the [Expression](#Expression) object.


pe.**<a id="match" href="#match">match</a>**
(*pattern, string, actions=None, parser='packrat', flags=pe.NONE*)

Match the parsing expression defined in *pattern* against the input
*string*.


pe.**<a id="escape" href="#escape">escape</a>**
(*string*)



pe.**<a id="unescape" href="#unescape">unescape</a>**
(*string*)


## Classes

*class* pe.core.**<a id="Parser" href="#Parser">Parser</a>**
(*grammar, flags=pe.NONE*)


pe.core.Parser.**<a id="Parser-match" href="#Parser-match">match</a>**
(*s, pos=0, flags=pe.NONE*)


*class* pe.core.**<a id="Match" href="#Match">Match</a>**
(*string, pos, end, pe, args, kwargs*)


## Exceptions

*class* pe.**<a id="Error" href="#Error">Error</a>**()


*class* pe.**<a id="GrammarError" href="#GrammarError">GrammarError</a>**()


*class* pe.core.**<a id="ParseError" href="#ParseError">ParseError</a>**
(*message=None, filename=None, lineno=None, offset=None, text=None*)


## Flags

The following constant values affect grammar compilation or matching
behavior.

pe.**<a id="NONE" href="#NONE">NONE</a>**

The flag used when no flags are set.


pe.**<a id="DEBUG" href="#DEBUG">DEBUG</a>**

Display the compiled grammar for debugging.


pe.**<a id="STRICT" href="#STRICT">STRICT</a>**

Raise an error on parse failures rather than returning `None`.


pe.**<a id="MEMOIZE" href="#MEMOIZE">MEMOIZE</a>**

Use memoization if the parser allows it.
