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
- Simple bindings with `val` and `var`, currently compiled as Erlang bindings/macros.
- Optional type annotations with basic inference.
- First-class concurrency primitives (`sp`, `send`, `receive`, `match`).
- Ergonomic pattern matching and map literals that translate to Erlang maps.
- Generated Erlang that follows idiomatic practices (macros for globals, explicit returns, `ok` fallbacks).
- Extensibility for richer data structures, modules, and a full semantic analysis phase.

---

## ✅ Current Features

- `val` declarations with optional type hints (`val total: int = 42`).
- `var` declarations with optional type hints (`var current: none = none`).
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
- Basic type checking and inference for `int`, `str`, `bool`, `none`, `pid`, and `dynamic`.
- CLI tool (`potionc`) that transpiles `.potion` files to `.erl` and optionally compiles/runs them.
- Example `.potion` programs under [`examples/`](./examples/).

---

## 🏗️ Language Building Blocks

### Global bindings
```potion
val rate = 5
val message = "Hello"
var maybe_name: none = none
```

→ Emitted as Erlang macros:
```erlang
-define(RATE, 5).
-define(MESSAGE, "Hello").
-define(MAYBE_NAME, undefined).
```

> ℹ️ Global names become `?MACROS` in Erlang; locals keep a Capitalized style (`Value`).
> `var` is currently supported as a declaration form, but not as reassignment syntax.

### Functions
```potion
fn calculate() {
    val next = rate + 3
    return next * 2
}
```

→ Erlang:
```erlang
calculate() ->
    Next = (?RATE + 3),
    (Next * 2).
```

### Types and `none`
```potion
var current: none = none
val ready: bool = true
val pid_ref: pid = self()
```

→ `none` is emitted as `undefined` in Erlang.

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
    receive msg {
        match msg {
            {hello: name, reply_to: caller} => {
                print("Hi, " + name)
                send(caller, {ok: "Message received"})
            }
        }
    }
}

fn main() {
    val pid = sp worker()
    send(pid, {hello: "Bruce", reply_to: self()})

    receive response {
        match response {
            {ok: text} => print(text)
            _ => print("No reply")
        }
    }
}
```

→ Erlang:
```erlang
worker() ->
    receive Msg ->
        case Msg of
            #{hello := Name, reply_to := Caller} ->
                io:format("~p~n", ["Hi, " ++ Name]),
                Caller ! #{ok => "Message received"}
        end
    end.

main() ->
    Pid = spawn(fun () -> worker() end),
    Pid ! #{hello => "Bruce", reply_to => self()},
    receive Response ->
        case Response of
            #{ok := Text} ->
                io:format("~p~n", [Text]);
            _ ->
                io:format("~p~n", ["No reply"])
        end
    end.
```

### Printing & strings
```potion
print("Total: " + result)
print("Age: " + to_string(age))
```

→ `io:format("~p~n", ["Total: " ++ Result])`

For a full list of reserved keywords, builtins, types, and syntax rules, see [`docs/language-spec.md`](./docs/language-spec.md).

### Current Syntax Summary

```potion
val total: int = 10
var fallback: none = none

fn main() {
    val approved: bool = total >= 5

    if approved {
        print("ok")
    } else {
        print("not ok")
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
- [ ] Reassignment / mutable update syntax for `var`.
- [ ] Lists, tuples, and richer collection literals.
- [ ] Module system and imports.
- [ ] Semantic analyser and static checks.
- [ ] Direct BEAM generation (skip intermediate Erlang).

---

## 📐 Current Limits

- Numeric literals are currently treated as integers in the parser and codegen.
- Function parameters do not have type annotations yet.
- `print(...)` currently expects a single argument.
- Map keys must be bare identifiers and are emitted as Erlang atoms.
- `var` supports declaration, but not reassignment syntax such as `x = y`.
- Type checking is intentionally lightweight and still tied to code generation.

---

## 🔥 Extended Example

```potion
val base: int = 10

fn worker() {
    receive msg {
        match msg {
            {compute: value, reply_to: caller} => {
                val doubled = value * 2
                send(caller, {result: doubled + base})
            }
        }
    }
}

fn main() {
    val pid = sp worker()
    send(pid, {compute: 5, reply_to: self()})

    receive response {
        match response {
            {result: total} => print("Result: " + total)
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
