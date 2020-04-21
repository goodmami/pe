# Change Log

## [Unreleased][unreleased]

### Added

* `pe.actions.Action`
* `pe.actions.Call`
* `pe.actions.Raw`
* `pe.actions.Bind`
* `pe.actions.Getter` (replaces `pe.actions.first` and `pe.actions.last`)

### Removed

* `pe.actions.first`
* `pe.actions.last`

### Changed

* Add `MEMOIZE` flag to grammar parser for better debugging
* Functions in `pe.actions` (`constant`, `pack`, `join`, `fail`) are now subclasses of `Action`: `Constant`, `Pack`, `Join`, `Fail`.


### Fixed

* Bug in definition formatting from partial reformatting


## [v0.1.0][]

**Release date: 2020-04-14**

This is the initial release with a functional Packrat recursive
descent parser and a work-in-progress state-machine parser.


[unreleased]: ../../tree/develop
[v0.1.0]: ../../releases/tag/v0.1.0
