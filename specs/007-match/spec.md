# Match

## Status

Implemented

## Goal

Define pattern matching over values, especially maps, with branch bodies.

## User-facing syntax

```potion
fn describe(person) {
    match person {
        {name: who, age: years} => {
            print("Name: " + who)
            print("Age: " + to_string(years))
        }
        _ => print("Unknown")
    }
}
```

## Tuple example

```potion
match value {
    {:ok, result} => print(result)
}
```

## Semantics

`match` compares a value against clauses in order. Supported current patterns include identifiers, `_`, integer, string, boolean, atom, `none`, map, tuple, and fixed-length list patterns. Identifier patterns bind values only within the clause body. Composite patterns can contain nested patterns. `=>` is the only Potion clause separator; `->` belongs exclusively to generated Erlang.

## Current implementation notes

`match` compiles to Erlang `case`. Map literal syntax is reused for map patterns and emitted with `:=` in patterns. Reassignment of local `var` bindings inside clauses is merged after the generated `case`.

The explicit pattern AST and the atom, tuple, and fixed-length list extensions are specified in `specs/016-pattern-matching/spec.md`.

## Guardrails

- list patterns match fixed-length lists; cons patterns are not implemented.
- There is no binary pattern matching today.

## Acceptance examples

```potion
match {ok: 2} {
    {ok: value} => print(value)
    _ => print("missing")
}
```

Expected current Erlang shape:

```erlang
case #{ok => 2} of
    #{ok := Value} ->
        io:format("~p~n", [Value]);
    _ ->
        io:format("~p~n", ["missing"])
end
```
