# Erlang codegen

## Status

Implemented

## Goal

Document the current Erlang backend as the active implementation target without making Erlang source generation the final required architecture.

## User-facing syntax

```potion
val base: int = 10

fn main() {
    val doubled = base * 2
    print(doubled)
}
```

## Pattern codegen example

```potion
match value {
    {:ok, result} => print(result)
}
```

Tuple patterns emit native Erlang tuple patterns. Fixed-length list patterns emit native Erlang list patterns.

## Semantics

The backend should preserve Potion source semantics when emitting executable code. Backend-specific names, helper functions, macros, and versioned variables are not visible in Potion source.

## Current implementation notes

The current backend emits `.erl` modules with `-module(...)` and `-export(...)`. Top-level values are emitted as Erlang macros. Functions become Erlang functions. `+` becomes Erlang `+` for integer addition and `++` for known string concatenation. `/` becomes `div`. Atoms emit as native Erlang atoms. Tuples emit as native Erlang tuples. Maps and lists emit as Erlang maps and lists. `if`, `match`, and `receive` emit as `case` or `receive`. External Erlang calls emit as `module:function(...)`.

## Guardrails

- Erlang macros for globals are an implementation choice.
- Erlang variable capitalization and version suffixes are backend details.
- Generated helpers such as `potion_to_string_builtin/1` are not final Potion APIs.
- Direct BEAM generation remains a possible future backend.

## Acceptance examples

```potion
val base: int = 10

fn double(value: int) {
    return value * 2
}
```

Expected current Erlang shape:

```erlang
-module(module_name).
-export([double/1]).

-define(BASE, 10).

double(Value) ->
    (Value * 2).
```
