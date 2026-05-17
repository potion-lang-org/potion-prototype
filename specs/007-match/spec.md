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

## Invalid examples

```potion
match value {
    {:ok, result} => print(result)
}
```

Tuple and atom literal patterns do not exist today.

## Semantics

`match` compares a value against clauses in order. Supported current patterns include identifiers, `_`, integer, string, boolean, `none`, and map patterns. Identifier patterns bind values for use in the clause body. Map patterns match required keys and nested patterns.

## Current implementation notes

`match` compiles to Erlang `case`. Map literal syntax is reused for map patterns and emitted with `:=` in patterns. Reassignment of local `var` bindings inside clauses is merged after the generated `case`.

## Guardrails

- Map-key atoms generated in Erlang are not Potion atom literals.
- There is no binary pattern matching today.
- There is no tuple pattern syntax today.
- Current use of `_` as an identifier pattern is parser/codegen convention, not a broader wildcard grammar.

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
