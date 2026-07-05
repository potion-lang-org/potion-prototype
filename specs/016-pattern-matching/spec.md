# Pattern Matching

## Status

Implemented

## Goal

Extend Potion's existing `match` control-flow expression with explicit pattern
AST nodes and initial structural patterns for values already supported by the
language.

This feature builds on the original map-oriented `match` described in
`specs/007-match/spec.md`.

## User-facing syntax

```potion
val message = match status {
    :ok => "success"
    :error => "failure"
    _ => "unknown"
}
```

Clause bodies may be expressions or blocks:

```potion
match value {
    0 => {
        print("zero")
    }
    _ => {
        print("other")
    }
}
```

Structural patterns may bind identifiers:

```potion
val message = match response {
    {:ok, value} => value
    {:error, reason} => reason
}
```

## Invalid examples

Patterns are not arbitrary expressions:

```potion
match value {
    expected + 1 => "invalid"
}
```

Function calls are not patterns:

```potion
match value {
    load() => "invalid"
}
```

The Erlang clause separator is not Potion syntax:

```potion
match value {
    :ok -> "invalid"
}
```

## Semantics

`match` evaluates its target once and selects the first compatible clause.

The initial pattern set is:

- `_`, which matches any value without creating a binding;
- integer, string, boolean, `none`, and atom literals;
- identifiers, which create branch-local bindings;
- map patterns;
- tuple patterns;
- fixed-length list patterns.

Literal patterns use structural equality. Composite patterns recursively apply
the same rules to their elements or entries. `[head, tail]` matches a list with
exactly two elements.

Identifier bindings exist only in the selected clause body. They do not leak
outside `match` and may shadow an outer source binding without changing it.

No exhaustiveness or unreachable-clause analysis is required in this phase.
When no clause matches, the runtime behavior follows the active backend's
non-exhaustive pattern-match behavior.

`=>` is the only clause separator accepted in Potion source. `->` is reserved
for the Erlang emitted by the current backend and must be rejected as Potion
syntax.

## Current implementation notes

The parser uses dedicated pattern nodes instead of parsing patterns as general
expressions. The semantic analyzer collects bindings recursively and validates
each body in an isolated branch scope.

The current Erlang backend emits `case ... of ... end`. Tuple and list patterns
emit native Erlang structural patterns. Branch bindings that shadow an outer
Potion binding receive an internal Erlang name to preserve Potion scoping.
These emitted names and the use of Erlang `case` are backend details.

## Compatibility

- Existing map patterns remain supported.
- Existing `=>` match clauses remain the official syntax.
- `->` is not accepted in Potion source.
- `if`, declarations, reassignment, functions, atoms, tuples, lists, Erlang
  imports, and receive patterns retain their previous syntax.

## Guardrails

- This phase does not add guards to `match`.
- This phase does not analyze exhaustiveness.
- This phase does not report unreachable clauses.
- Cons, improper-list, binary, and map-rest patterns are not implemented.
- Fixed-length list patterns are the current initial subset, not a permanent
  restriction on Potion's future list pattern design.
- Erlang pattern syntax and runtime errors are implementation details of the
  current backend, not the final language architecture.

## Acceptance examples

```potion
fn main() {
    val response = {:ok, "Potion"}
    val message = match response {
        {:ok, value} => value
        {:error, reason} => reason
    }
    print(message)
}
```

Expected current Erlang shape:

```erlang
main() ->
    Response = {ok, "Potion"},
    Message = case Response of
        {ok, Value} ->
            Value;
        {error, Reason} ->
            Reason
    end,
    io:format("~p~n", [Message]).
```
