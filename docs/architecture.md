# Potion Architecture Notes

This document summarizes the current compiler pipeline in this repository.

It is intentionally short and reflects the implementation that exists today.

## Pipeline

The public CLI runs this flow:

1. Read the entry `.potion` file
2. Load sibling imported Potion modules
3. Tokenize and parse each module into an AST
4. Run semantic analysis and type checks needed by code generation
5. Emit Erlang source for each module
6. Optionally call `erlc` to produce `.beam`
7. Optionally run `main/0` through `erl -noshell`

## Main Components

### Lexer

[`lexer/potion_lexer.py`](../lexer/potion_lexer.py) tokenizes Potion source into the tokens consumed by the parser.

Current scope includes:

- keywords
- identifiers
- literals
- operators
- delimiters used by functions, maps, lists, and control-flow blocks

### Parser

[`parser/potion_parser.py`](../parser/potion_parser.py) builds the AST.

Current AST coverage includes:

- top-level declarations
- functions and parameters
- imports
- literals and expressions
- `if` / `else`
- `match`
- `sp`, `send`, and `receive`
- assignments for function-local `var`

### Semantic Analysis

[`semantic/potion_semantic.py`](../semantic/potion_semantic.py) performs the current validation pass before code generation.

Current responsibilities include:

- tracking declared names and function arities
- validating explicit type annotations
- lightweight type inference
- validating `var` reassignment
- checking string concatenation rules
- checking that Erlang modules were imported before external calls
- handling the binding conventions used by `receive`

### Code Generation

[`codegen/potion_codegen.py`](../codegen/potion_codegen.py) walks the AST and emits Erlang source.

Current conventions include:

- top-level `val` becomes Erlang macros
- local identifiers become capitalized Erlang variables
- mutable `var` becomes versioned Erlang variables
- `if` and `match` become Erlang `case`
- `receive` becomes Erlang `receive`
- external module calls become `module:function(...)`

### CLI

[`cli/potionc.py`](../cli/potionc.py) is the entry point exposed as `potionc`.

Current CLI responsibilities:

- validate the input path
- load the module graph
- emit `.erl` files to `target/` or a custom output directory
- call `erlc` unless `--no-beam` is set
- optionally print the AST with `--emit-ast`
- optionally run `main/0` with `--run`

## Current Boundaries

- Potion currently generates Erlang first; it does not emit BEAM directly
- module loading is currently limited to sibling `.potion` files
- Erlang interop is explicit and intentionally minimal
- the semantic phase is practical, not a full standalone type system
