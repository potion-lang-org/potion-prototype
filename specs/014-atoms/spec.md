# Atoms

## Status

Implemented

## Goal

Add symbolic immutable values to Potion using `:`-prefixed atom literals.

Atoms are useful for statuses, tags, options, and simple symbolic results while preserving direct interop with Erlang atoms.

## User-facing syntax

```potion
val status = :ok
val error: atom = :error
var env: atom = :prod

fn get_status() {
    return :ok
}

fn main() {
    print(:ok)
}
```

## Invalid examples

```potion
val empty = :
val number = :123
val invalid = :Invalid
val dashed = :hello-world
val status: int = :ok
```

## Semantics

Atoms represent immutable symbolic values. Atom literals use the form `:identifier`; the stored value is the identifier without the `:` prefix.

Valid atom names must start with a lowercase letter or underscore and may contain letters, numbers, and underscores after that.

Atoms have type `atom`. They may be used in declarations, function arguments, function calls, `print`, equality comparisons, `return`, comparisons used by `if` expressions, and map values. `:ok == :ok` is true, while `:ok == :error` is false.

Potion atoms map directly to Erlang atoms. `:ok` in Potion emits `ok` in Erlang.

## Current implementation notes

The lexer recognizes valid atom literals as `ATOM` tokens. The parser stores them as `LiteralAtom(value)` nodes with the value excluding `:`. The semantic analyzer uses a lightweight `AtomValue` placeholder to infer and validate the `atom` type. Erlang codegen emits simple atom names without quotes and emits quoted Erlang atoms, not strings, when required for names such as `:_private` or `:receive`.

`print(:ok)` uses the existing Erlang `io:format("~p~n", ...)` path. `to_string(:ok)` uses the existing generated Erlang helper path for atoms through `atom_to_list/1`.

## Guardrails

- Atom literals do not add tuple syntax.
- Atom literals are supported as literal patterns in `match`.
- Atom literals do not add binary pattern matching.
- Atom literals do not add lambdas or Erlang fun syntax.
- Atom literals do not change `receive` syntax.
- Erlang helper code remains an implementation detail, not Potion standard library design.
- Erlang remains the current backend, not the mandatory final backend.

## Acceptance examples

```potion
fn get_status() {
    return :ok
}

fn main() {
    val status: atom = get_status()

    if status == :ok {
        print("status ok")
    } else {
        print("status error")
    }

    print(:not_found)
}
```

Expected current Erlang shape includes:

```erlang
get_status() ->
    ok.

main() ->
    Status = get_status(),
    case (Status == ok) of
        true ->
            io:format("~p~n", ["status ok"]);
        _ ->
            io:format("~p~n", ["status error"])
    end,
    io:format("~p~n", [not_found]).
```
