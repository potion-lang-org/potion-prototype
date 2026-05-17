# Semantic analysis

## Status

Partially implemented

## Goal

Document the current static checks Potion performs before or during code generation.

## User-facing syntax

```potion
fn greet(name: str) {
    print(name)
}

fn main() {
    greet("Bruce")
}
```

## Invalid examples

```potion
val message = "Age: " + 42
```

```potion
fn main() {
    var total: int = 1
    total = "wrong"
}
```

```potion
fn main() {
    httpc.request("https://example.com")
}
```

## Semantics

Potion should reject clear static errors such as unknown variables, unsupported type annotations, invalid reassignment, incompatible string/integer `+`, wrong argument counts for known Potion functions, mismatched annotated argument types when known, and Erlang module calls without an explicit import.

## Current implementation notes

Semantic checks are implemented in `SemanticAnalyzer` and reused by `ErlangCodegen`. The analyzer tracks function arities, local variables, global values, mutable `var` bindings, simple inferred types, known parameter annotations, and imported Erlang modules. Many complex expressions are treated as dynamic.

## Guardrails

- Current dynamic fallbacks are implementation limits, not final type-system design.
- Erlang interop validation stops at checking the import.
- Static analysis is intentionally lightweight today and should not be documented as complete soundness.
- The analyzer's Python placeholder values are not Potion runtime values.

## Acceptance examples

```potion
fn greet(name: str) {
    print(name)
}

fn main() {
    greet(1)
}
```

Expected current result: compilation fails with a typed function-call error for `greet`.
