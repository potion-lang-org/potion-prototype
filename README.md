# Potion Language — Design Document

> 🇧🇷 [Versão em Português](./README-pt-br.md)  
> 🤝 [Contributing (EN)](./.github/CONTRIBUTING.en.md) • [Contribuindo (PT-BR)](./.github/CONTRIBUTING.pt-br.md)  
> 📜 [Code of Conduct (EN)](./.github/CODE_OF_CONDUCT.en.md) • [Código de Conduta (PT-BR)](./.github/CODE_OF_CONDUCT.pt-br.md)

---

## 📖 Overview

**Potion** is a minimalist language inspired by Python, Erlang, and Rust, designed for learning, experimentation, and generating Erlang code from a simple and expressive syntax.  
Its goal is to make writing business logic clear and safe, producing efficient code for concurrent environments like the BEAM/Erlang VM.

---

## ✨ Goals

- Clean syntax, similar to modern languages (e.g., Python, Rust).
- Support for immutable (`val`) and future mutable (`var`) variables.
- Pure functions and side-effect functions (e.g., `print`).
- Simple conditionals (`if`, `else`).
- Basic types: integers, booleans, strings.
- Compilation to readable Erlang using best practices (`ok`, proper block endings, correct use of local/global variables).
- Future extensibility: lists, maps, pattern matching, modules.

---

## 🏗️ Language Structure

### Global Variables

```potion
val x = 5
val name = "João"
```

→ Translates to Erlang macros:

```erlang
-define(X, 5).
-define(NAME, "João").
```

---

### Functions

```potion
fn calculate() {
    val y = x + 3
    return y * 2
}
```

→ Translates to Erlang:

```erlang
calculate() ->
    Y = (?X + 3),
    (Y * 2).
```

---

### Conditionals (`if`, `else`)

```potion
fn check() {
    if value > 0 {
        print("Greater than zero")
    } else {
        print("Less than or equal to zero")
    }
}
```

→ Translates to Erlang:

```erlang
check() ->
    case (?VALUE > 0) of
        true ->
            io:format("~p~n", ["Greater than zero"]);
        _ ->
            io:format("~p~n", ["Less than or equal to zero"])
    end.
```

---

### Printing

```potion
print("Hello World")
```

→ Erlang:

```erlang
io:format("~p~n", ["Hello World"])
```

---

## 🛠️ Compiler Architecture

- **Parser** → Builds the AST (Abstract Syntax Tree).
- **Codegen** → Walks through the AST and emits Erlang code.
- **Transpiler** → Uses the above modules to transform `.potion` → `.erl`.

---

## ⚡ Roadmap (Upcoming Features)

- [ ] Optional typing: `val x: int = 5`
- [ ] Mutable variables: `var counter = 0`
- [ ] Compound structures: lists, maps
- [ ] Pattern matching
- [ ] Modules and imports
- [ ] Official CLI for compilation and execution

---

## 🔥 Full Example

```potion
val base = 10

fn sum_values() {
    val a = base + 5
    val b = a * 2
    return b + 3
}

fn main() {
    sum_values()
}
```

→ Erlang:

```erlang
-define(BASE, 10).

sum_values() ->
    A = (?BASE + 5),
    B = (A * 2),
    (B + 3).

main() ->
    sum_values().
```

---

## 📜 Philosophy

- **Clarity over magic:** Explicit code beats obscure automation.
- **Educational focus:** Helps new programmers understand compilers and code generation.
- **Interop-friendly:** Seamlessly integrates with the Erlang ecosystem.