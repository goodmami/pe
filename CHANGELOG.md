# Change Log

## [Unreleased][unreleased]

### Fixed

* Group quantized 2+ char literals in regex optimization ([#54])


## [v0.5.3][]

**Release date: 2024-06-18**

### Added

* `pe.operators.Repeat` ([#46])
* `e{n}` and `e{m,n}` syntax ([#46])

### Changed

* Bounded repetitions via `e{n}` and `e{m,n}` forms ([#46])


## [v0.5.2][]

**Release date: 2024-03-28**

### Fixed

* Optimization returns new grammar instead of mutating original ([#44])
* Make union of choice of character classes ([#44])
* `Flag.STRICT` now raises parsing errors in machine parser


## [v0.5.1][]

**Release date: 2023-12-31**

### Python Support

* Added support for Python 3.12

### Fixed

* Repetitions with mincount > 0 no longer reuse the instruction object ([#38])

### Maintenance

* Use pyproject.toml instead of setup.cfg for project metadata
* Use Ruff for linting ([#36])
* Update CI workflows, including OIDC trusted publishing


## [v0.5.0][]

**Release date: 2023-07-26**

### Added

* `pe.operators.AutoIgnore` ([#6])
* `pe.patterns` module ([#6])
* `pe.patterns.DEFAULT_IGNORE` ([#6])
* `ignore` parameter on `pe.compile()`, `pe.match()`,
  `pe.packrat.PackratParser`, and `pe.machine.MachineParser` ([#6])

### Changed

* Line-breaking whitespace and tabs are escaped in debug context string ([#31])


## [v0.4.0][]

**Release date: 2023-06-04**

### Python Support

* Removed support for Python 3.6, 3.7 ([#23])
* Added support for Python 3.10, 3.11 ([#23])

### Fixed

* Parse errors on loading a grammar are now GrammarError ([#21])


## [v0.3.2][]

**Release date: 2021-10-05**

### Fixed

* Regex optimization avoids some superfluous groups ([#19])

### Changed

* Added more 'common' optimations: ([#20])
  - Single-character classes become literals
  - Sequence of literals becomes one literal
  - Choice of non-negated character classes become one class


## [v0.3.1][]

**Release date: 2021-09-30**

### Added

* `pe.Parser.modified_grammar` attribute

### Removed

* `pe.scanners` is no longer part of the public API

### Changed

* Debug mode now prints the modified grammar when it has been
  optimized

### Fixed

* Capture choices properly in the machine parser ([#17])
* Character classes better handle multiple ranges ([#18])


## [v0.3.0][]

**Release date: 2021-09-28**

### Added

* `pe.Match.span()` ([#12])
* `pe.actions.Pair` ([#13])
* `negate` parameter on `pe.operators.Class`
* "Common" optimizations (currently only negated character classes)
  via the `pe.COMMON` flag
* `pe.scanners` module for the low-level text scanners

### Changed

* Changed `pe.Match.pos` to `pe.Match.start()` ([#12])
* Changed `pe.Match.end` to `pe.Match.end()` ([#12])
* `-` is no longer an escapable character
* `pe.machine` is now distributed as a compiled extension module

### Fixed

* `pe.machine` is now working again and passing the tests


## [v0.2.0][]

**Release date: 2020-04-28**

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
[v0.2.0]: ../../releases/tag/v0.2.0
[v0.3.0]: ../../releases/tag/v0.3.0
[v0.3.1]: ../../releases/tag/v0.3.1
[v0.3.2]: ../../releases/tag/v0.3.2
[v0.4.0]: ../../releases/tag/v0.4.0
[v0.5.0]: ../../releases/tag/v0.5.0
[v0.5.1]: ../../releases/tag/v0.5.1
[v0.5.2]: ../../releases/tag/v0.5.2
[v0.5.3]: ../../releases/tag/v0.5.3

[#6]: https://github.com/goodmami/pe/issues/6
[#7]: https://github.com/goodmami/pe/issues/7
[#9]: https://github.com/goodmami/pe/issues/9
[#12]: https://github.com/goodmami/pe/issues/12
[#13]: https://github.com/goodmami/pe/issues/13
[#17]: https://github.com/goodmami/pe/issues/17
[#18]: https://github.com/goodmami/pe/issues/18
[#19]: https://github.com/goodmami/pe/issues/19
[#20]: https://github.com/goodmami/pe/issues/20
[#21]: https://github.com/goodmami/pe/issues/21
[#23]: https://github.com/goodmami/pe/issues/23
[#31]: https://github.com/goodmami/pe/issues/31
[#36]: https://github.com/goodmami/pe/issues/36
[#38]: https://github.com/goodmami/pe/issues/38
[#44]: https://github.com/goodmami/pe/issues/44
[#46]: https://github.com/goodmami/pe/issues/46
[#54]: https://github.com/goodmami/pe/issues/54
