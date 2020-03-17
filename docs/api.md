
# API Reference

> **Note:** This document is a reference for the full API. See the
> [tutorial](tutorial.md) for information about usage.


## pe


pe.**<a id="pe-match" href="#pe-match">match</a>**
(*pattern, string, action=None, actions=None, parser='packrat', flags=0*)

pe.**<a id="pe-compile" href="#pe-compile">compile</a>**
(*source, action=None, actions=None, parser='packrat', flags=0*)

pe.**<a id="pe-escape" href="#pe-escape">escape</a>**
(*string*)

pe.**<a id="pe-unescape" href="#pe-unescape">unescape</a>**
(*string*)

*class* pe.**<a id="pe-error" href="#pe-error">Error</a>**


## pe.actions

pe.actions.**<a id="pe-constant" href="#pe-constant">constant</a>**
(*value*)

pe.actions.**<a id="pe-pack" href="#pe-pack">pack</a>**
(*func*)

pe.actions.**<a id="pe-join" href="#pe-join">join</a>**
(*func, sep=''*)

pe.actions.**<a id="pe-first" href="#pe-first">first</a>**
(*\*args, \*\*kwargs*)

pe.actions.**<a id="pe-last" href="#pe-last">last</a>**
(*\*args, \*\*kwargs*)


## pe.constants

(not currently documented)


## pe.core

*class* pe.core.**<a id="pe-core-Error" href="#pe-core-Error">Error</a>**

*class* pe.core.**<a id="pe-core-ParseError" href="#pe-core-ParseError">ParseError</a>**
(*message=None, filename=None, lineno=None, offset=None, text=None*)

*class* pe.core.**<a id="pe-core-Match" href="#pe-core-Match">Match</a>**
(*string, pos, end, pe, args, kwargs*)

*class* pe.core.**<a id="pe-core-Expression" href="#pe-core-Expression">Expression</a>**

pe.core.Expression.**<a id="pe-core-Expression-match" href="#pe-core-Expression-match">match</a>**
(*s, pos=0, flags=pe.NONE*)

*class* pe.core.**<a id="pe-core-Definition" href="#pe-core-Definition">Definition</a>**
(*op, args*)

*class* pe.core.**<a id="pe-core-Grammar" href="#pe-core-Grammar">Grammar</a>**
(*definitions=None, actions=None, start='Start'*)

pe.core.**<a id="pe-core-evaluate" href="#pe-core-evaluate">evaluate</a>**
(*args, value_type*)


## pe.grammar

pe.grammar.**<a id="pe-grammar-load" href="#pe-grammar-load">load</a>**
(*source*)

pe.grammar.**<a id="pe-grammar-loads" href="#pe-grammar-loads">loads</a>**
(*source, flags=pe.NONE*)

pe.grammar.**<a id="pe-grammar-Dot" href="#pe-grammar-Dot">Dot</a>**
(**)

pe.grammar.**<a id="pe-grammar-Literal" href="#pe-grammar-Literal">Literal</a>**
(*string*)

pe.grammar.**<a id="pe-grammar-Class" href="#pe-grammar-Class">Class</a>**
(*chars*)

pe.grammar.**<a id="pe-grammar-Regex" href="#pe-grammar-Regex">Regex</a>**
(*pattern, flags=0*)

pe.grammar.**<a id="pe-grammar-Sequence" href="#pe-grammar-Sequence">Sequence</a>**
(*\*expressions*)

pe.grammar.**<a id="pe-grammar-Choice" href="#pe-grammar-Choice">Choice</a>**
(*\*expressions*)

pe.grammar.**<a id="pe-grammar-Repeat" href="#pe-grammar-Repeat">Repeat</a>**
(*expression, min=0, max=-1*)

pe.grammar.**<a id="pe-grammar-Optional" href="#pe-grammar-Optional">Optional</a>**
(*expression*)

pe.grammar.**<a id="pe-grammar-Star" href="#pe-grammar-Star">Star</a>**
(*expression*)

pe.grammar.**<a id="pe-grammar-Plus" href="#pe-grammar-Plus">Plus</a>**
(*expression*)

pe.grammar.**<a id="pe-grammar-Nonterminal" href="#pe-grammar-Nonterminal">Nonterminal</a>**
(*name*)

pe.grammar.**<a id="pe-grammar-And" href="#pe-grammar-And">And</a>**
(*expression*)

pe.grammar.**<a id="pe-grammar-Not" href="#pe-grammar-Not">Not</a>**
(*expression*)

pe.grammar.**<a id="pe-grammar-Discard" href="#pe-grammar-Discard">Discard</a>**
(*expression*)

pe.grammar.**<a id="pe-grammar-Bind" href="#pe-grammar-Bind">Bind</a>**
(*expression, name=None*)

pe.grammar.**<a id="pe-grammar-Rule" href="#pe-grammar-Rule">Rule</a>**
(*expression, action*)


## pe.machine

*class* pe.machine.**<a id="pe-machine-parser" href="#pe-machine-parser">Parser</a>**
(*grammar*)


## pe.packrat

*class* pe.packrat.**<a id="pe-packrat-parser" href="#pe-packrat-parser">Parser</a>**
(*grammar*)
