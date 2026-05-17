# Print and to_string

## Status

POC workaround

## Goal

Provide minimal user-facing output and explicit textual conversion while the language does not yet have a standard library design.

## User-facing syntax

```potion
fn main() {
    val age: int = 42
    print("Age: " + to_string(age))
}
```

## Invalid examples

```potion
print("Age: ", 42)
```

```potion
val age: int = 42
val message = "Age: " + age
```

## Semantics

`print(value)` writes a representation of one value. `to_string(value)` explicitly converts a value to a string-like value suitable for textual concatenation. Potion does not implicitly coerce integers or booleans to strings for `+`.

## Current implementation notes

`print` is parsed specially and requires exactly one argument. Codegen emits `io:format("~p~n", [Value])`. `to_string` is parsed as a normal function call but treated specially by semantic analysis and codegen. When used, codegen appends an Erlang helper named `potion_to_string_builtin/1`.

## Guardrails

- `io:format("~p~n", ...)` formatting is not final Potion output design.
- `potion_to_string_builtin/1` is a generated Erlang helper, not a stable standard-library API.
- Current conversion behavior follows Erlang runtime categories and should not be treated as final cross-backend semantics.

## Acceptance examples

```potion
fn main() {
    print("Total = " + to_string(3))
}
```

Expected current Erlang shape includes:

```erlang
io:format("~p~n", [("Total = " ++ potion_to_string_builtin(3))])
```
