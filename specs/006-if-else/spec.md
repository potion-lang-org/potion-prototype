# If else

## Status

Implemented

## Goal

Define conditional control flow with optional `else` blocks.

## User-facing syntax

```potion
fn classify(score) {
    if score >= 7 {
        print("approved")
    } else {
        print("rejected")
    }
}
```

## Invalid examples

```potion
if true
    print("missing braces")
```

## Semantics

An `if` evaluates its condition and runs the true branch when the condition is true. Otherwise it runs the `else` branch when present, or an empty fallback branch when omitted. Mutable variables reassigned inside branches remain available after the conditional with a merged value.

## Current implementation notes

`if` compiles to an Erlang `case` over the condition, matching `true` and `_`. Branch reassignment of local `var` bindings is compiled by returning updated values from each branch and binding a merge variable after the `case`.

## Guardrails

- The Erlang `case` shape is backend detail.
- Current condition validation is lightweight; do not treat missing strict boolean enforcement as final semantics.
- Merge variables are not part of Potion source semantics.

## Acceptance examples

```potion
fn main() {
    var total: int = 1
    if true {
        total = total + 2
    } else {
        total = total + 10
    }
    print(total)
}
```

Expected current Erlang shape includes:

```erlang
Total_2 = case true of
    true ->
        Total_1 = (Total_0 + 2),
        Total_1;
    _ ->
        Total_1 = (Total_0 + 10),
        Total_1
end
```
