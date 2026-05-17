# Functions

## Status

Implemented

## Goal

Define Potion function declarations, positional parameters, calls, and returns.

## User-facing syntax

```potion
fn double(value: int) {
    return value * 2
}

fn main() {
    val result: int = double(10)
    print(result)
}
```

## Invalid examples

```potion
fn greet(name: unknown_type) {
    print(name)
}
```

```potion
fn greet(name: str) {
    print(name)
}

fn main() {
    greet(1)
}
```

## Semantics

Functions have a name, positional parameters, optional parameter type annotations, and a block body. `return` explicitly produces the function result. If there is no explicit `return` as the last statement, the last expression emitted by the function body is the current result.

## Current implementation notes

Functions are collected before code generation. Local function calls validate arity and annotated argument types when enough static information is available. Imported sibling functions can be called directly and are emitted as remote Erlang calls.

## Guardrails

- There are no lambdas, anonymous functions, closures, or first-class functions today.
- Function overloading is not defined as a language feature.
- Current return behavior follows codegen behavior and may need a more explicit final design.

## Acceptance examples

```potion
fn sum(a: int, b: int) {
    return a + b
}
```

Expected current Erlang shape:

```erlang
sum(A, B) ->
    (A + B).
```
