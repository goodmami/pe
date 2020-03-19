
# API Reference: pe.grammar

## Functions

pe.grammar.**<a id="load" href="#load">load</a>**
(*source*)

pe.grammar.**<a id="loads" href="#loads">loads</a>**
(*source, flags=pe.NONE*)


## Classes

*class* pe.core.**<a id="Definition" href="#Definition">Definition</a>**
(*op, args*)


*class* pe.core.**<a id="Grammar" href="#Grammar">Grammar</a>**
(*definitions=None, actions=None, start='Start'*)


## Operator Functions

pe.grammar.**<a id="Dot" href="#Dot">Dot</a>**()

pe.grammar.**<a id="Literal" href="#Literal">Literal</a>**
(*string*)

pe.grammar.**<a id="Class" href="#Class">Class</a>**
(*chars*)

pe.grammar.**<a id="Regex" href="#Regex">Regex</a>**
(*pattern, flags=0*)

pe.grammar.**<a id="Sequence" href="#Sequence">Sequence</a>**
(*\*expressions*)

pe.grammar.**<a id="Choice" href="#Choice">Choice</a>**
(*\*expressions*)

pe.grammar.**<a id="Repeat" href="#Repeat">Repeat</a>**
(*expression, min=0, max=-1*)

pe.grammar.**<a id="Optional" href="#Optional">Optional</a>**
(*expression*)

pe.grammar.**<a id="Star" href="#Star">Star</a>**
(*expression*)

pe.grammar.**<a id="Plus" href="#Plus">Plus</a>**
(*expression*)

pe.grammar.**<a id="Nonterminal" href="#Nonterminal">Nonterminal</a>**
(*name*)

pe.grammar.**<a id="And" href="#And">And</a>**
(*expression*)

pe.grammar.**<a id="Not" href="#Not">Not</a>**
(*expression*)

pe.grammar.**<a id="Raw" href="#Raw">Raw</a>**
(*expression*)

pe.grammar.**<a id="Discard" href="#Discard">Discard</a>**
(*expression*)

pe.grammar.**<a id="Bind" href="#Bind">Bind</a>**
(*expression, name=None*)

pe.grammar.**<a id="Rule" href="#Rule">Rule</a>**
(*expression, action*)
