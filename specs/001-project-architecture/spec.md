# Project architecture

## Status

Implemented

## Goal

Describe the current Potion compiler pipeline and repository shape without making the current Python or Erlang implementation a permanent language requirement.

## User-facing syntax

```potion
import helpers
import erlang lists

fn main() {
    print(lists.reverse([1, 2, 3]))
}
```

## Invalid examples

```potion
import nested.helpers
```

Nested module paths are not supported by the current loader.

## Semantics

A Potion program is organized as one `.potion` source file per module. A source file may import sibling Potion modules and explicitly imported Erlang modules. The compiler should parse source, validate it, and produce an executable representation without exposing accidental implementation details as part of the language contract.

## Current implementation notes

The CLI accepts a `.potion` entry file, loads sibling imports, tokenizes, parses, runs semantic checks through code generation, emits `.erl` files, and optionally runs `erlc` and `erl`. Potion modules are loaded from the same directory as the importing file. Generated Erlang module names are sanitized from file names.

## Guardrails

- Python is the current compiler implementation language, not part of the Potion language design.
- Erlang source generation is the current backend, not a mandatory final backend.
- Sibling-only imports are a current loader limitation, not a final module-system decision.
- Generated Erlang module-name sanitization is an implementation detail.

## Acceptance examples

```potion
// helpers.potion
fn greet(name: str) {
    print(name)
}
```

```potion
// main.potion
import helpers

fn main() {
    greet("Bruce")
}
```

Expected current Erlang shape:

```erlang
main() ->
    helpers:greet("Bruce").
```
