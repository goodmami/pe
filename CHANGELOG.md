# Change Log

## [Unreleased][unreleased]

### Added

* `pe.GrammarWarning` ([#7])
* `pe.actions.Action`
* `pe.actions.Call`
* `pe.actions.Raw`
* `pe.actions.Bind`
* `pe.actions.Getter` (replaces `pe.actions.first` and `pe.actions.last`)
* `pe.actions.Warn` ([#7])
* `pe.operators.Debug` ([#9])

### Removed

* `pe.actions.first`
* `pe.actions.last`
* Concept of "value types" from specification and implementation
* `pe.Grammar.finalize()` and `pe.Grammar.final`

### Changed

* Add `MEMOIZE` flag to grammar parser for better debugging
* Functions in `pe.actions` (`constant`, `pack`, `join`, `fail`) are now subclasses of `Action`: `Constant`, `Pack`, `Join`, `Fail`.
* `pe.compile()` no longer takes an open file or a single definition as input
* Grammar vs Expression parsing is more consistent internally
* Packrat parser handles the Debug operator ([#9])
* Grammar parser now warns on unlikely range ([#7])
* Rename "raw" to "capture" throughout

### Fixed

* Bug in definition formatting from partial reformatting


## [v0.1.0][]

**Release date: 2020-04-14**

This is the initial release with a functional Packrat recursive
descent parser and a work-in-progress state-machine parser.


[unreleased]: ../../tree/develop
[v0.1.0]: ../../releases/tag/v0.1.0

[#7]: https://github.com/goodmami/pe/issues/7
[#9]: https://github.com/goodmami/pe/issues/9
