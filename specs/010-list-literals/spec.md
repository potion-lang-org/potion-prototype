# List literals

## Status

Implemented

## Goal

Define ordered list literals for Potion values and Erlang interop.

## User-facing syntax

```potion
val empty = []
val numbers = [1, 2, 3]

fn main() {
    print(numbers)
}
```

## Invalid examples

```potion
val improper = [head | tail]
```

Cons-cell and improper-list syntax are not implemented.

## Semantics

A list literal evaluates to an ordered sequence of values. Lists may be empty and may contain expressions. Potion currently does not enforce homogeneous element types.

## Current implementation notes

The parser has a `ListLiteral` AST node. Codegen emits Erlang list syntax directly. The semantic analyzer evaluates elements for validation but treats the list as dynamic.

## Guardrails

- Direct Erlang list emission is a backend detail.
- No final list type syntax, element type checking, pattern matching, or cons syntax is defined yet.
- Lists being Erlang strings in some contexts is an Erlang interop fact, not a complete Potion string/list design.

## Acceptance examples

```potion
import erlang lists

fn main() {
    val reversed = lists.reverse([1, 2, 3])
    print(reversed)
}
```

Expected current Erlang shape:

```erlang
Reversed = lists:reverse([1, 2, 3]),
io:format("~p~n", [Reversed])
```
