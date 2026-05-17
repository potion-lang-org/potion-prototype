# Lexical syntax

## Status

Implemented

## Goal

Define the currently accepted lexical surface for identifiers, literals, comments, punctuation, and reserved words.

## User-facing syntax

```potion
// a comment
val name: str = "Potion"
val enabled: bool = true
val count: int = 42
```

Reserved words include `return`, `val`, `var`, `import`, `erlang`, `fn`, `sp`, `send`, `receive`, `on`, `when`, `any`, `match`, `none`, `if`, `else`, `true`, and `false`.

## Invalid examples

```potion
val @name = 1
```

```potion
val path = module-name
```

## Semantics

Identifiers name bindings, functions, modules, map keys, and receive tags. Whitespace separates tokens and is otherwise insignificant. Line comments begin with `//` and continue to the end of the line.

## Current implementation notes

The lexer is regex-based. Identifiers use `[a-zA-Z_][a-zA-Z0-9_]*`. Strings use double quotes. Integer-looking numbers are parsed as `LiteralInt`; the lexer pattern also accepts decimal-looking numbers, but the parser currently converts number tokens with `int(...)`.

## Guardrails

- Decimal tokenization must not be documented as implemented float support.
- The current permissive string regex is not a complete final string-literal design.
- No atom, tuple, binary, char, or interpolation syntax exists today.

## Acceptance examples

```potion
val total: int = 10
val message: str = "hello"
val ok: bool = false
```

Expected current token categories include `VAL`, `ID`, `COLON`, `ID`, `ASSIGN`, `NUMBER`, `STRING`, and `BOOL`.
