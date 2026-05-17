# Val and var bindings

## Status

Implemented

## Goal

Define immutable-style `val` bindings and function-local mutable `var` bindings.

## User-facing syntax

```potion
val base: int = 10

fn main() {
    val label: str = "Total"
    var total: int = base
    total = total + 2
    print(label + ": " + to_string(total))
}
```

## Invalid examples

```potion
fn main() {
    val total: int = 1
    total = 2
}
```

```potion
var global_total: int = 1
global_total = 2
```

## Semantics

`val` introduces a binding that cannot be reassigned. `var` introduces a mutable binding intended for function-local state. Reassigning a `var` must preserve the established type when that type is known.

## Current implementation notes

Top-level `val` and top-level `var` are both currently collected as Erlang macros, but module-level mutable state is not part of the language model. Local `var` reassignment is compiled by generating versioned Erlang variables such as `Total_0`, `Total_1`, and merge variables after control-flow blocks.

## Guardrails

- Top-level `var` macro emission is not design approval for global mutable state.
- Erlang versioned variable names are a backend workaround.
- Merge-variable codegen is not user-facing syntax.

## Acceptance examples

```potion
fn main() {
    var total: int = 1
    total = total + 2
    print(total)
}
```

Expected current Erlang shape:

```erlang
main() ->
    Total_0 = 1,
    Total_1 = (Total_0 + 2),
    io:format("~p~n", [Total_1]).
```
