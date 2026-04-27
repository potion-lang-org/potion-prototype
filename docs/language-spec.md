# Potion Language Specification

This document describes the current implemented surface of Potion in this repository.

It is a practical reference for the compiler as it exists today, not a future-facing proposal.

## Overview

Potion is a small language that compiles to Erlang source code and then to BEAM bytecode through the existing CLI flow.

Current implementation focus:

- top-level `val` declarations
- function-local mutable bindings with `var`
- functions and explicit `return`
- arithmetic and comparisons
- maps, lists, and pattern matching
- process spawning and message passing
- lightweight type annotations and inference
- semantic analysis before Erlang code generation
- Erlang interop through imported modules

## Reserved Keywords

The lexer currently reserves these keywords:

- `return`
- `val`
- `var`
- `import`
- `erlang`
- `fn`
- `sp`
- `send`
- `receive`
- `on`
- `when`
- `any`
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
- list literals, for example `[1, 2, 3]`

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

At module level, `val` is the only supported declaration form.

### `var`

Function-local mutable binding form supported by the compiler:

```potion
var current = none
var current: none = none
```

Local reassignment is supported:

```potion
fn accumulate() {
    var total: int = 1
    total = total + 1
    total = total * 3
    print("Total = " + to_string(total))
}
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
val rate = 5
val message = "hello"
```

becomes:

```erlang
-define(RATE, 5).
-define(MESSAGE, "hello").
```

Local bindings inside functions are emitted as capitalized Erlang variables.

```potion
fn calculate(delta: int) {
    val next = rate + delta
    return next
}
```

becomes:

```erlang
calculate(Delta) ->
    Next = (?RATE + Delta),
    Next.
```

For mutable local `var`, the compiler internally emits versioned Erlang variables to preserve Erlang's single-assignment model.

## Functions

Function declaration syntax:

```potion
fn sum(a: int, b: int) {
    return a + b
}
```

Current rules:

- parameters are positional
- parameter type annotations are optional
- explicit `return` is supported
- if the last statement is not a `return`, the last emitted Erlang expression becomes the function result

Example with mixed annotated and unannotated parameters:

```potion
fn greet(name: str, suffix) {
    return name + suffix
}
```

## Modules And Imports

Potion uses one source file per module.

### Importing sibling Potion modules

```potion
import module_helpers

fn main() {
    greet("Bruce")
    announce("Bruce", 42)
}
```

Current rules:

- `import module_name` resolves to `module_name.potion`
- imported modules are searched in the same directory as the importing file
- imported functions can be called directly by name in Potion source
- imported calls are emitted as remote Erlang calls such as `module_helpers:greet(...)`
- local functions take precedence over imported functions with the same name and arity

Current limitations:

- imported `.potion` modules expose functions, not imported top-level `val` bindings
- there is no alias syntax and no selective import syntax
- nested directory module paths are not implemented

### Importing Erlang modules

```potion
import erlang math
import erlang lists

fn main() {
    val root = math.sqrt(16)
    val reversed = lists.reverse([1, 2, 3])
    print(root)
    print(reversed)
}
```

Current rules:

- `import erlang module_name` registers an external Erlang module for the current file
- external Erlang calls use the form `module_name.function_name(...)`
- external Erlang calls are emitted as `module_name:function_name(...)`
- the semantic analyzer checks whether the Erlang module was imported before use

Current limitations:

- Erlang interop does not validate module existence, function existence, or arity
- Potion still has no atom literal syntax, so some Erlang APIs are callable but not fully ergonomic yet

## Expressions

Supported expression forms:

- identifiers
- function calls
- external module calls in the form `module.function(...)`
- arithmetic
- comparisons
- map literals
- list literals
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
- `+` accepts `int + int` and `str + str`
- mixed `+` expressions such as `str + int` and `int + str` are rejected at compile time
- use `to_string(...)` explicitly when you need textual concatenation with a non-string value
- string concatenation becomes `++` in Erlang after semantic validation confirms both sides are strings

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

Typical use:

```potion
send(worker_pid, {hello: "Bruce", reply_to: self()})
```

`reply_to` is not a reserved keyword. It is just the current message-shape convention used by the compiler's `receive` sugar.

### `to_string(value)`

Converts a value to a string-like Erlang list.

```potion
val age: int = 42
print("Age: " + to_string(age))
```

Current conversion behavior:

- strings and lists: unchanged
- integers: `integer_to_list/1`
- booleans: converted from atoms
- `none` / `undefined`: `"undefined"`
- atoms: `atom_to_list/1`
- binaries: `binary_to_list/1`
- fallback: `io_lib:format("~p", ...)` flattened to a list

Potion favors explicit conversion over implicit coercion.

This is invalid:

```potion
val age: int = 42
val message = "Age: " + age
```

This is valid:

```potion
val age: int = 42
val message = "Age: " + to_string(age)
```

## Semantic Analysis

Before Erlang code generation, Potion runs a semantic analysis phase.

Current responsibilities:

- record declared names and function arities
- track local mutable `var` bindings
- infer simple value types when possible
- validate explicit type annotations
- reject invalid reassignment
- reject incompatible `+` operations such as `str + int`
- ensure Erlang module calls reference modules imported through `import erlang`

Type checking is intentionally lightweight and tied to the current compiler pipeline.

## Control Flow

### `if / else`

```potion
fn classify(score) {
    val approved: bool = score >= 7

    if approved {
        print("approved")
    } else {
        print("rejected")
    }
}
```

This is emitted as an Erlang `case` on the condition.

When mutable `var` bindings are reassigned inside branches, the compiler emits a merge step after the `case` so later expressions can refer to the updated value.

Example:

```potion
fn main() {
    var total: int = 1

    if true {
        total = total + 2
    } else {
        total = total + 10
    }

    print("Total = " + to_string(total))
}
```

## `none`

`none` is the language-level spelling for the absence of a value.

```potion
var current: none = none
```

It is emitted as Erlang `undefined`.

Example:

```potion
var current: none = none
val fallback: str = "anonymous"

fn describe(name) {
    if name == none {
        print("Missing name")
    } else {
        print("Name: " + name)
    }
}
```

## Maps, Lists, And Pattern Matching

### Map literals

```potion
val person = {name: "Bruce", age: 42}
```

Map keys are currently bare identifiers and become Erlang atoms.

Nested maps are supported:

```potion
val request = {
    user: {name: "Bruce"},
    meta: {source: "api"}
}
```

### List literals

```potion
val numbers = [1, 2, 3]
print(numbers)
```

Lists are especially useful when interoperating with Erlang modules such as `lists`.

### `match`

```potion
match person {
    {name: who, age: years} => {
        print("Name: " + who)
        print("Age: " + to_string(years))
    }
    _ => print("unknown")
}
```

Supported pattern forms:

- identifier bindings
- `_` wildcard
- literal integers, strings, and booleans
- `none`
- nested map patterns

Example with nested patterns:

```potion
match request {
    {user: {name: who}, meta: {source: source}} => {
        print("User: " + who)
        print("Source: " + source)
    }
    _ => print("invalid request")
}
```

Notes:

- a pattern key like `age` binds whatever is on the right-hand side, for example `age: years`
- after that pattern, the bound variable is `years`, not `age`
- `match` compiles to an Erlang `case`
- if mutable `var` bindings are reassigned inside `match` branches, the compiler merges the final version after the control-flow expression

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

### `receive`

```potion
receive {
    on ok(text) {
        print(text)
    }

    on any {
        print("unexpected")
    }
}
```

Compiles to an Erlang `receive ... end`.

Inside `receive`, `on <tag>(arg1, arg2, ...)` is sugar for map pattern matching.

Current binding convention:

- the first binding maps to the payload under the message tag
- the next binding maps to `reply_to`
- `on any` compiles to the fallback `_` clause
- optional `when` expressions compile to Erlang guards

Example:

```potion
fn worker() {
    receive {
        on hello(name, caller) {
            print("Hello, " + name)
            send(caller, {ok: "received"})
        }

        on any {
            print("unexpected message")
        }
    }
}

fn main() {
    val proc_id: pid = sp worker()
    send(proc_id, {hello: "Bruce", reply_to: self()})

    receive {
        on ok(text) {
            print(text)
        }

        on any {
            print("no response")
        }
    }
}
```

Example with a guard:

```potion
receive {
    on data(value, caller) when value > 10 {
        send(caller, {ok: value})
    }

    on any {
        print("ignored")
    }
}
```

If mutable `var` bindings are reassigned inside `receive` bodies, the compiler merges the final version after the control-flow expression.

## Erlang HTTP Interop

Potion can call Erlang modules directly after an explicit import.

```potion
import erlang ssl
import erlang inets
import erlang httpc

fn main() {
    ssl.start()
    inets.start()

    val response = httpc.request("https://datatrail.com.br")
    print(response)
}
```

This compiles to remote Erlang calls such as `ssl:start()`, `inets:start()`, and `httpc:request(...)`.

For HTTPS requests, `ssl.start()` must run before `httpc.request(...)`.

The feature-server demo under [`../demo/`](../demo/) uses this same interop approach together with Erlang bridge code for HTTP and Mnesia operations.

## Code Generation Rules

Current important codegen conventions:

- top-level declarations become Erlang macros
- local identifiers become capitalized Erlang variables
- local mutable `var` bindings become versioned Erlang variables
- `if` becomes `case`
- `match` becomes `case`
- map literals become Erlang maps
- list literals become Erlang lists
- map patterns use `:=`
- string concatenation uses `++`
- `print(...)` emits `io:format("~p~n", [...])`
- external module calls become `module:function(...)`

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
- parameter type annotations are optional, but return type annotations are not implemented
- imports across `.potion` files are limited to sibling modules and imported functions
- imported `.potion` modules do not expose imported global `val` bindings
- Erlang interop is limited to `import erlang <module>` and `<module>.<function>(...)`
- Erlang interop does not validate module existence, function existence, or arity
- there is no tuple syntax yet
- there is no atom literal syntax yet
- type checking is lightweight and still tied to code generation
- string concatenation depends on the compiler recognizing the expression as string-producing
- there is no direct BEAM generation; Potion generates Erlang first
