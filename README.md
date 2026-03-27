# Potion Language — Design Document

> 🇧🇷 [Versão em Português](./README-pt-br.md)  
> 🤝 [Contributing (EN)](./.github/CONTRIBUTING.en.md) • [Contribuindo (PT-BR)](./.github/CONTRIBUTING.pt-br.md)  
> 📜 [Code of Conduct (EN)](./.github/CODE_OF_CONDUCT.en.md) • [Código de Conduta (PT-BR)](./.github/CODE_OF_CONDUCT.pt-br.md)
> 📘 [Language Spec (EN)](./docs/language-spec.md) • [Especificação da Linguagem (PT-BR)](./docs/language-spec.pt-br.md)

---

## 📖 Overview

**Potion** is a minimalist language inspired by Python, Go, Erlang, and Rust, designed for learning, experimentation, and generating Erlang code from a simple and expressive syntax.  
Its goal is to make writing business logic clear and safe, producing efficient code for concurrent environments such as the BEAM/Erlang VM.

---

## ✨ Goals

- Modern, lightweight syntax (Python/Rust vibes) that targets Erlang/OTP.
- Simple bindings with `val` and local mutable bindings with `var`.
- Optional type annotations with basic inference.
- First-class concurrency primitives (`sp`, `send`, `receive`, `match`).
- Ergonomic pattern matching and map literals that translate to Erlang maps.
- Generated Erlang that follows idiomatic practices (macros for globals, explicit returns, `ok` fallbacks).
- Extensibility for richer data structures and modules, on top of the current semantic analysis phase.

---

## ✅ Current Features

- `val` declarations with optional type hints (`val total: int = 42`).
- `var` declarations with optional type hints (`var current: none = none`).
- Function parameters with optional type hints (`fn greet(name: str, age: int) { ... }`).
- Local reassignment for `var` with syntax like `current = next_value`.
- Module imports between `.potion` files with `import module_name`.
- Functions with parameters, local bindings, and explicit `return`.
- Literals for integers, strings, booleans, maps, and `none`.
- Arithmetic (`+`, `-`, `*`, `/`) and comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`).
- String concatenation with `+`, emitted as `++` in Erlang.
- `if` / `else` conditionals compiled to Erlang `case` expressions.
- Map literals and nested pattern matching via `match` blocks.
- Concurrency building blocks: spawning processes with `sp`, sending messages with `send`, and awaiting them via `receive`.
- Built-in `self()` support for obtaining the current Erlang process id.
- Built-in `to_string(...)` for stringifying values before concatenation.
- Built-in `print(...)` that maps to `io:format`.
- Dedicated semantic analysis with type checking and inference for `int`, `str`, `bool`, `none`, `pid`, and `dynamic`.
- CLI tool (`potionc`) that transpiles `.potion` files to `.erl` and optionally compiles/runs them.
- Example `.potion` programs under [`examples/`](./examples/).

---

## 🏗️ Language Building Blocks

### Global bindings
```potion
val rate = 5
val message = "Hello"
```

→ Emitted as Erlang macros:
```erlang
-define(RATE, 5).
-define(MESSAGE, "Hello").
```

> ℹ️ Global names become `?MACROS` in Erlang; locals keep a Capitalized style (`Value`).
> Potion uses `val` for module-level bindings and `var` for mutable local state inside functions.

### Functions
```potion
fn calculate(delta: int) {
    val next = rate + delta
    return next * 2
}
```

→ Erlang:
```erlang
calculate(Delta) ->
    Next = (?RATE + Delta),
    (Next * 2).
```

### Modules and imports
```potion
import module_helpers

fn main() {
    greet("Bruce")
}
```

Potion resolves `import module_helpers` to `module_helpers.potion` in the same directory as the importing file.
Imported function calls are written without qualification in Potion and emitted as remote Erlang calls internally.

### Types and `none`
```potion
val current: none = none
val ready: bool = true
val pid_ref: pid = self()
```

→ `none` is emitted as `undefined` in Erlang.

### `var` reassignment
```potion
fn accumulate() {
    var total: int = 1
    total = total + 2
    print(total)
}
```

Potion compiles local `var` reassignment to versioned Erlang variables internally.
That preserves Erlang's single-assignment semantics while exposing mutable-style syntax at the Potion level.

### Conditionals
```potion
fn check(score) {
    if score > 0 {
        print("Positive")
    } else {
        print("Zero or negative")
    }
}
```

→ Erlang:
```erlang
check(Score) ->
    case (Score > 0) of
        true ->
            io:format("~p~n", ["Positive"]);
        _ ->
            io:format("~p~n", ["Zero or negative"])
    end.
```

### Map literals & pattern matching
```potion
fn describe(person) {
    match person {
        {name: who, age: years} => print("Name: " + who)
        _ => print("Unknown person")
    }
}
```

→ Erlang:
```erlang
describe(Person) ->
    case Person of
        #{name := Who, age := Years} ->
            io:format("~p~n", ["Name: " ++ Who]);
        _ ->
            io:format("~p~n", ["Unknown person"])
    end.
```

> 🔒 Keys must currently be bare identifiers (emitted as atoms) and values can nest other maps or identifiers.

### Concurrency (`sp`, `send`, `receive`, `match`)
```potion
fn worker() {
    receive {
        on hello(name, caller) {
            print("Hi, " + name)
            send(caller, {ok: "Message received"})
        }

        on any {
            print("Unexpected message")
        }
    }
}

fn main() {
    val pid = sp worker()
    send(pid, {hello: "Bruce", reply_to: self()})

    receive {
        on ok(text) {
            print(text)
        }

        on any {
            print("No reply")
        }
    }
}
```

→ Erlang:
```erlang
worker() ->
    receive
        #{hello := Name, reply_to := Caller} ->
            io:format("~p~n", ["Hi, " ++ Name]),
            Caller ! #{ok => "Message received"};
        _ ->
            io:format("~p~n", ["Unexpected message"])
    end.

main() ->
    Pid = spawn(fun () -> worker() end),
    Pid ! #{hello => "Bruce", reply_to => self()},
    receive
        #{ok := Text} ->
            io:format("~p~n", [Text]);
        _ ->
            io:format("~p~n", ["No reply"])
    end.
```

### Printing & strings
```potion
print("Total: " + to_string(result))
print("Age: " + to_string(age))
```

→ `io:format("~p~n", ["Total: " ++ potion_to_string_builtin(Result)])`

Potion does not perform implicit coercion for mixed `+` expressions.
This is rejected at compile time:

```potion
val age: int = 42
val message = "Age: " + age
```

Use `to_string(...)` explicitly when you want textual concatenation:

```potion
val message = "Age: " + to_string(age)
```

For a full list of reserved keywords, builtins, types, and syntax rules, see [`docs/language-spec.md`](./docs/language-spec.md).

### Current Syntax Summary

```potion
val total: int = 10
var fallback: none = none

fn main() {
    var approved: bool = false
    approved = total >= 5

    if approved {
        print("ok")
    } else {
        print("not ok")
    }

    receive {
        on ok(message) {
            print(message)
        }

        on any {
            print("ignored")
        }
    }
}
```

Supported type names today:

- `int`
- `str`
- `bool`
- `none`
- `pid`
- `dynamic`

---

## 🧰 CLI (`potionc`)

`potionc` is a Python entry point that lives under `cli/potionc.py`.

**Requirements**
- Python 3.8+
- Erlang/OTP (`erlc` and `erl` on your PATH)

**Installation**
```bash
# development workflow: keep the command pointing at your local checkout
pip install -e .

# regular install
pip install .
```

After `pip install -e .`, changes in the compiler source are picked up by the installed `potionc` command without reinstalling after every edit.

**Usage**
```bash
python -m cli.potionc path/to/file.potion [options]
# after installing with `pip install -e .` or `pip install .` you can simply run:
potionc path/to/file.potion [options]
```

**Options**
- `--outdir DIR` – directory for generated `.erl`/`.beam` files (default: `target/`).
- `--no-beam` – skip Erlang compilation, emit only the `.erl` file.
- `--emit-ast` – print the parsed AST instead of generating code.
- `--run` – after successful compilation, executes `module:main/0` inside `erl -noshell`.

**Examples**
```bash
# Transpile and compile
python -m cli.potionc exemplo.potion

# Generate only the .erl
python -m cli.potionc send_message.potion --no-beam

# Compile to a custom folder and run main/0
python -m cli.potionc send_message.potion --outdir build --run

# install the CLI in editable mode for development
pip install -e .
```

---

## 🛠️ Compiler Architecture

- **Lexer** → Tokenizes Potion source code.
- **Parser** → Produces an AST with declarations, literals, control flow, and concurrency nodes.
- **Codegen** → Walks the AST and emits human-friendly Erlang.
- **CLI** → Glue that orchestrates parsing, code generation, `erlc`, and optional execution.

---

## ⚡ Roadmap

- [x] Optional typing on `val` declarations.
- [x] Optional typing on `var` declarations.
- [x] `none` literal support.
- [x] Map literals with basic pattern matching.
- [x] Concurrency primitives (`sp`, `send`, `receive`, `match`).
- [x] Official CLI for transpile/compile/run.
- [x] Reassignment / mutable update syntax for local `var`.
- [x] Optional typing on function parameters.
- [x] Basic module imports across `.potion` files in the same directory.
- [ ] Lists, tuples, and richer collection literals.
- [x] Semantic analyser and static checks.
- [ ] Direct BEAM generation (skip intermediate Erlang).

---

## 📐 Current Limits

- Numeric literals are currently treated as integers in the parser and codegen.
- `print(...)` currently expects a single argument.
- Map keys must be bare identifiers and are emitted as Erlang atoms.
- `var` is intended for function-local mutable state, not module-level mutable state.
- Type checking is intentionally lightweight and still incomplete compared to a full standalone type system.
- Imports currently resolve only to sibling `.potion` files and expose imported functions, not imported global values.

---

## 🔥 Extended Example

```potion
val base: int = 10

fn worker() {
    receive {
        on compute(value, caller) {
            val doubled = value * 2
            send(caller, {result: doubled + base})
        }

        on any {
            print("unexpected")
        }
    }
}

fn main() {
    val pid = sp worker()
    send(pid, {compute: 5, reply_to: self()})

    receive {
        on result(total) {
            print("Result: " + to_string(total))
        }

        on any {
            print("No reply")
        }
    }
}
```

→ Emits Erlang with macros, capitalized locals, map patterns, and message passing ready for the BEAM VM.

---

## 📜 Philosophy

- **Clarity over magic:** explicit transformations keep the learning curve gentle.
- **Pedagogical focus:** demystify compilers, ASTs, and the BEAM toolchain.
- **Interop first:** generated Erlang should play nicely with existing OTP code bases.

> 🧪 Potion is still experimental; expect breaking changes while the language evolves.
