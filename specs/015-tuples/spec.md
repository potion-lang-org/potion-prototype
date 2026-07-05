# Tuples

## Status

Implemented

## Goal

Add immutable positional values to Potion that map directly to Erlang tuples.

Tuples prioritize Erlang/OTP interoperability, simple status/result shapes, and future compatibility with pattern matching and OTP abstractions.

## User-facing syntax

```potion
val result = {:ok, 123}
val error = {:error, "not found"}
val nested = {:ok, {:user, 10}}

print({:ok, 42})
```

## Invalid examples

```potion
val trailing = {:ok,}
val missing_first = {,123}
```

`{}` remains the existing empty map literal, not an empty tuple.

## Semantics

Tuples are immutable ordered values. They preserve positional order and can contain expressions such as integers, booleans, strings, atoms, lists, tuples, variables, and function calls. Float values are intended tuple elements once Potion has real float literal support; the current parser still does not represent floats as a separate AST type.

Tuples have type `tuple`. Potion supports tuple destructuring in `match`
patterns. It does not currently support tuple arity validation, structural
tuple types, tuple indexing, records, or named tuples.

Potion tuples map directly to Erlang tuples. `{:ok, 123}` in Potion emits `{ok, 123}` in Erlang. Tuples are not converted to maps or lists.

## Current implementation notes

The lexer reuses existing `{`, `}`, and `,` tokens. The parser distinguishes braced literals as follows:

- `{}` parses as the existing empty map literal.
- `{name: value}` parses as a map literal.
- `{expr, expr...}` parses as `TupleLiteral(elements)`.

The semantic analyzer recognizes `tuple` as a primitive type and uses a lightweight `TupleValue` placeholder for inference and simple equality. The Erlang backend emits native Erlang tuple syntax directly.

Tuple literals can contain any expression that the current expression parser already supports. This feature does not add float literal support.

## Guardrails

- Tuple destructuring is limited to `match` patterns.
- This feature does not add tuple indexing.
- This feature does not add named tuples, records, or structs.
- This feature does not add advanced tuple typing such as `tuple<int, str>`.
- This feature does not add OTP abstractions.
- This feature does not change `receive` syntax or semantics.
- Erlang tuples are the current backend representation, not a new helper library.

## Acceptance examples

```potion
fn get_result() {
    return {:ok, 42}
}

fn wrap(value) {
    return {:reply, value}
}

fn main() {
    val result: tuple = get_result()
    val nested = {:ok, {:user, 10}}
    val with_call = {:wrapped, wrap(10)}

    print(result)
    print(nested)
    print(with_call)
}
```

Expected current Erlang shape includes:

```erlang
get_result() ->
    {ok, 42}.

Nested = {ok, {user, 10}},
With_call = {wrapped, wrap(10)}
```
