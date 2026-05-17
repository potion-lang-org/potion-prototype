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
val person = {name: "Bruce", age: 42}
val numbers = [1, 2, 3]
```

## Invalid examples

```potion
val ratio: float = 1.5
```

```potion
val status = :ok
val pair = {ok, 1}
```

## Semantics

Potion currently exposes `int`, `str`, `bool`, `none`, `pid`, and `dynamic` as accepted type names. `none` represents absence of a value. Maps hold key-value data, with current source keys written as bare identifiers. Lists hold ordered values.

## Current implementation notes

The semantic analyzer maps known type names to simple Python placeholder values. `none` is emitted as Erlang `undefined`. Map keys are emitted as Erlang atoms. Most nontrivial expressions, list literals, map literals, receives, matches, sends, and Erlang interop calls are treated as dynamic by the analyzer.

## Guardrails

- `dynamic` is mainly a current analyzer escape hatch, not a finished type-system design.
- Erlang atoms created from map keys do not mean Potion has atom literals.
- Map support does not imply tuple support.
- Current integer-only numeric behavior should not be treated as the final numeric tower.

## Acceptance examples

```potion
val person = {name: "Bruce", age: 42}
val missing: none = none
```

Expected current Erlang shape:

```erlang
-define(PERSON, #{name => "Bruce", age => 42}).
-define(MISSING, undefined).
```
