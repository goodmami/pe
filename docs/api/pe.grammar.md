
# API Reference: pe.grammar

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
