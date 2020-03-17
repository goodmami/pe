
# API Reference: pe.core


*class* pe.core.**<a id="Error" href="#Error">Error</a>**

*class* pe.core.**<a id="ParseError" href="#ParseError">ParseError</a>**
(*message=None, filename=None, lineno=None, offset=None, text=None*)

*class* pe.core.**<a id="Match" href="#Match">Match</a>**
(*string, pos, end, pe, args, kwargs*)

*class* pe.core.**<a id="Expression" href="#Expression">Expression</a>**

pe.core.Expression.**<a id="Expression-match" href="#Expression-match">match</a>**
(*s, pos=0, flags=pe.NONE*)

*class* pe.core.**<a id="Definition" href="#Definition">Definition</a>**
(*op, args*)

*class* pe.core.**<a id="Grammar" href="#Grammar">Grammar</a>**
(*definitions=None, actions=None, start='Start'*)

pe.core.**<a id="evaluate" href="#evaluate">evaluate</a>**
(*args, value_type*)
