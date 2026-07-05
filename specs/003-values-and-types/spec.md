# Values and types

## Status

Partially implemented

## Goal

Describe Potion's current value forms and lightweight type model while leaving room for a richer type system later.

## User-facing syntax

```potion
val age: int = 42
val name: str = "Bruce"
val active: bool = true
val missing: none = none
val status: atom = :ok
val result: tuple = {:ok, 42}
val person = {name: "Bruce", age: 42}
val numbers = [1, 2, 3]
```

## Invalid examples

```potion
val ratio: float = 1.5
```

## Semantics

Potion currently exposes `int`, `str`, `bool`, `none`, `atom`, `tuple`, `pid`, and `dynamic` as accepted type names. `none` represents absence of a value. Atoms represent symbolic immutable values. Tuples represent immutable positional values. Maps hold key-value data, with current source keys written as bare identifiers. Lists hold ordered values.

## Current implementation notes

The semantic analyzer maps known type names to simple Python placeholder values. `none` is emitted as Erlang `undefined`. Potion atom literals such as `:ok` are emitted as Erlang atoms such as `ok`. Tuple literals such as `{:ok, 42}` are emitted as Erlang tuples such as `{ok, 42}`. Map keys are emitted as Erlang atoms. Most nontrivial expressions, list literals, map literals, receives, matches, sends, and Erlang interop calls are treated as dynamic by the analyzer.

## Guardrails

- `dynamic` is mainly a current analyzer escape hatch, not a finished type-system design.
- Erlang atoms created from map keys are separate from Potion's `:atom` literal syntax.
- Tuple destructuring is currently available in `match`; tuple indexing and structural tuple typing are not implemented.
- Current integer-only numeric behavior should not be treated as the final numeric tower.

## Acceptance examples

```potion
val person = {name: "Bruce", age: 42}
val missing: none = none
val status: atom = :ok
val result: tuple = {:ok, 42}
```

Expected current Erlang shape:

```erlang
-define(PERSON, #{name => "Bruce", age => 42}).
-define(MISSING, undefined).
-define(STATUS, ok).
-define(RESULT, {ok, 42}).
```
