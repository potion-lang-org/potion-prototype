# Potion Language Specification

This document describes the current implemented surface of the Potion language in this repository.

It is a practical reference for the compiler as it exists today, not a future-facing proposal.

## Overview

Potion is a small language that compiles to Erlang source code.

Current implementation focus:

- simple declarations with `val` and local mutable bindings with `var`
- functions and returns
- arithmetic and comparisons
- maps and pattern matching
- message passing and process spawning
- lightweight type annotations and inference

## Reserved Keywords

The lexer currently reserves these keywords:

- `return`
- `val`
- `var`
- `fn`
- `sp`
- `send`
- `receive`
- `match`
- `none`
- `if`
- `else`
- `true`
- `false`

Special builtins that are parsed as regular identifiers but treated specially by the compiler:

- `print`
- `self`
- `to_string`

## Supported Types

Current type names accepted by the compiler:

- `int`
- `str`
- `bool`
- `none`
- `pid`
- `dynamic`

Notes:

- `none` maps to Erlang `undefined`
- `pid` is intended for process ids such as the result of `self()` or `sp ...`
- `dynamic` is used internally for values whose static type is not known precisely

## Literals

Supported literals:

- integer literals, for example `42`
- string literals, for example `"hello"`
- boolean literals: `true`, `false`
- `none`
- map literals, for example `{name: "Bruce", age: 42}`

Current limitations:

- numeric literals are parsed as integers
- floating-point syntax is tokenized by the lexer but not represented as a separate numeric AST type
- map keys must be bare identifiers

## Declarations

### `val`

Immutable-style declaration form:

```potion
val total = 10
val total: int = 10
```

### `var`

Function-local mutable binding form supported by the compiler:

```potion
var current = none
var current: none = none
```

Local reassignment is supported:

```potion
var total: int = 1
total = total + 1
```

Important:

- reassignment is supported for local `var` bindings inside functions
- `var` is intended for function-local mutable state
- module-level mutable global state is not part of the language model
- assigning to a `val` is rejected by the compiler
- reassignment preserves the previously established type of the variable

### Global vs local bindings

Top-level bindings are expressed with `val` and are emitted as Erlang macros:

```potion
val base = 10
```

becomes:

```erlang
-define(BASE, 10).
```

Local bindings inside functions are emitted as capitalized Erlang variables.
For mutable local `var`, the compiler internally emits versioned Erlang variables to preserve Erlang's single-assignment model.

## Functions

Function declaration syntax:

```potion
fn sum(a, b) {
    return a + b
}
```

Current rules:

- parameters are positional
- parameters do not have type annotations yet
- explicit `return` is supported
- if the last statement is not a `return`, the last emitted Erlang expression becomes the function result

## Expressions

Supported expression forms:

- identifiers
- function calls
- arithmetic
- comparisons
- map literals
- `if` blocks
- `match` blocks
- `receive` blocks
- `send(...)`
- `sp ...`
- assignment statements for previously declared local `var`

### Operators

Arithmetic operators:

- `+`
- `-`
- `*`
- `/`

Comparison operators:

- `==`
- `!=`
- `<`
- `>`
- `<=`
- `>=`

Notes:

- `/` is emitted as Erlang integer division `div`
- string concatenation uses `+` in Potion and becomes `++` in Erlang when the compiler recognizes a string expression

## Builtins

### `print(value)`

Prints one value using Erlang `io:format`.

```potion
print("hello")
print(total)
```

Current rule:

- exactly one argument

### `self()`

Returns the current Erlang process id.

```potion
val me: pid = self()
```

### `to_string(value)`

Converts a value to a string-like Erlang list.

```potion
print("Age: " + to_string(age))
```

Current conversion behavior:

- strings/lists: unchanged
- integers: `integer_to_list/1`
- booleans: converted from atoms
- `none` / `undefined`: `"undefined"`
- atoms: `atom_to_list/1`
- binaries: `binary_to_list/1`
- fallback: `io_lib:format("~p", ...)` flattened to a list

## Control Flow

### `if / else`

```potion
if score > 0 {
    print("positive")
} else {
    print("zero or negative")
}
```

This is emitted as an Erlang `case` on the condition.
When mutable `var` bindings are reassigned inside branches, the compiler emits a merge step after the `case` so later expressions can refer to the updated value.

## Maps and Pattern Matching

### Map literals

```potion
val person = {name: "Bruce", age: 42}
```

### `match`

```potion
match person {
    {name: who, age: years} => print(who)
    _ => print("unknown")
}
```

Supported pattern forms:

- identifier bindings
- `_` wildcard
- literal integers, strings and booleans
- `none`
- nested map patterns

Notes:

- a pattern key like `age` binds whatever is on the right-hand side, for example `age: years`
- after that pattern, the bound variable is `years`, not `age`

## Concurrency

Potion currently exposes a small Erlang-style concurrency surface.

### `sp`

```potion
val pid: pid = sp worker()
```

Compiles to Erlang `spawn(fun () -> worker() end)`.

### `send(target, message)`

```potion
send(pid, {ok: "done"})
```

Compiles to Erlang `!`.

`send` only sends a value to a target process. It does not create an automatic reply channel.

If the sender expects a response, the common pattern is to include its own pid in the message:

```potion
send(worker_pid, {hello: "Bruce", reply_to: self()})
```

The receiver can then bind that pid in a map pattern and reply explicitly:

```potion
match message {
    {hello: name, reply_to: caller} => {
        send(caller, {ok: "received"})
    }
}
```

Notes:

- `self()` returns the pid of the current process
- `reply_to` is not a reserved keyword; it is a conventional map key
- `caller` is not a reserved keyword; it is just the local binding name used in the pattern
- this is a message protocol convention built on top of `send`, not a special reply feature of the language

### `receive`

```potion
receive message {
    match message {
        {ok: text} => print(text)
    }
}
```

Compiles to an Erlang `receive ... end`.
If mutable `var` bindings are reassigned inside `receive` bodies or nested `match` clauses, the compiler merges the final version after the control-flow expression.

## Code Generation Rules

Current important codegen conventions:

- top-level declarations become Erlang macros
- local identifiers become capitalized Erlang variables
- local mutable `var` bindings become versioned Erlang variables
- `if` becomes `case`
- `match` becomes `case`
- map literals become Erlang maps
- map patterns use `:=`
- string concatenation uses `++`
- `print(...)` emits `io:format("~p~n", [...])`

## CLI Naming Rules

The CLI derives the Erlang module name from the source filename.

If the filename is not a valid Erlang module atom form, it is sanitized:

- invalid characters become `_`
- the name is lowercased
- if it does not start with a letter, it is prefixed with `potion_`

Example:

- `01_values_and_functions.potion`
- becomes Erlang module `potion_01_values_and_functions`

## Current Limitations

- module-level mutable state is not part of the language
- parameter type annotations are not implemented
- there is no module/import system
- there are no lists or tuples in Potion syntax yet
- type checking is lightweight and still tied to code generation
- string concatenation depends on the compiler recognizing the expression as string-producing
- there is no direct BEAM generation; Potion generates Erlang first
