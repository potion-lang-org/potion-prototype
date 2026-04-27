# Potion

Experimental language for the BEAM with simple syntax, explicit concurrency, and Erlang interop.

Potion is a small language project built to compile `.potion` source into Erlang and run on the BEAM today. It exists as a practical experiment in language design, compiler construction, and concurrent application structure, not as a replacement for Erlang or Elixir. The current compiler already handles a real `.potion -> .erl -> .beam` pipeline and includes a working feature-server demo under [`demo/`](./demo/).

> 🇧🇷 [Versão em Português](./README-pt-br.md)  
> 📘 [Language Spec (EN)](./docs/language-spec.md) • [Especificação da Linguagem (PT-BR)](./docs/language-spec.pt-br.md)  
> 🏗️ [Architecture Notes](./docs/architecture.md)  
> 🤝 [Contributing (EN)](./.github/CONTRIBUTING.en.md) • [Contribuindo (PT-BR)](./.github/CONTRIBUTING.pt-br.md)  
> 📜 [Code of Conduct (EN)](./.github/CODE_OF_CONDUCT.en.md) • [Código de Conduta (PT-BR)](./.github/CODE_OF_CONDUCT.pt-br.md)

## Why Potion Exists

Potion exists to explore what a smaller, more direct language for BEAM-targeted programs can feel like in practice:

- simple syntax for business logic and message-passing workflows
- explicit concurrency with `sp`, `send`, and `receive`
- straightforward Erlang interop instead of pretending the BEAM ecosystem does not exist
- a real compiler pipeline that stays readable enough for experimentation and learning

Potion is not trying to replace Erlang or Elixir. The current direction is narrower: a practical experiment in simplicity, concurrency, and interop on top of Erlang/OTP.

## What Works Today

- Compile `.potion` source into `.erl`, then into `.beam`
- Functions, `val`, function-local `var`, and explicit `return`
- Basic type annotations and lightweight semantic checks
- Maps, lists, `if`/`else`, `match`, and `none`
- Imports between sibling `.potion` modules
- Erlang interop via `import erlang <module>`
- Concurrency with `sp`, `send`, `receive`, and `self()`
- CLI workflow through `potionc`
- A real feature-server demo under [`demo/`](./demo/)

## Real Demo

The fastest proof that Potion is already doing real work is the feature-server POC in [`demo/`](./demo/). It compiles Potion modules, uses Erlang support code for HTTP/Mnesia, and coordinates requests through a concurrent manager process.

Run it from the `demo/` directory:

```bash
cd demo
potionc --run main.potion
```

The demo currently expects `demo_support.erl` to be available by relative path, so running it from inside `demo/` is the practical path today.

Then hit the server on `http://localhost:4040`:

```bash
curl -i -X POST http://localhost:4040/features \
  -H 'content-type: application/json' \
  -d '{
    "name": "new_checkout",
    "environment": "prod",
    "enabled": true,
    "description": "new checkout flow"
  }'
```

Representative response:

```json
{
  "name": "new_checkout",
  "environment": "prod",
  "enabled": true,
  "description": "new checkout flow",
  "updated_at": "2026-04-13T12:34:56Z"
}
```

```bash
curl -i "http://localhost:4040/features/new_checkout?environment=prod"
```

```json
{
  "name": "new_checkout",
  "environment": "prod",
  "enabled": true,
  "description": "new checkout flow",
  "updated_at": "2026-04-13T12:34:56Z"
}
```

```bash
curl -i http://localhost:4040/features
```

```json
[
  {
    "name": "new_checkout",
    "environment": "prod",
    "enabled": true,
    "description": "new checkout flow",
    "updated_at": "2026-04-13T12:34:56Z"
  }
]
```

More demo details live in [`demo/README.md`](./demo/README.md).

## Quick Language Taste

Function and local bindings:

```potion
val base: int = 10

fn sum(delta: int) {
    var total: int = base
    total = total + delta
    return total
}
```

Concurrency:

```potion
fn worker() {
    receive {
        on hello(name, caller) {
            send(caller, {ok: "hello " + name})
        }
    }
}

fn main() {
    val pid: pid = sp worker()
    send(pid, {hello: "Bruce", reply_to: self()})
}
```

Interop with Erlang modules:

```potion
import erlang lists

fn main() {
    print(lists.reverse([1, 2, 3]))
}
```

For syntax and semantics in detail, use [`docs/language-spec.md`](./docs/language-spec.md).

## Install And Run

Requirements:

- Python 3.8+
- Erlang/OTP with `erlc` and `erl` on `PATH`

Install for development:

```bash
pip install -e .
```

Basic usage:

```bash
potionc examples/01_values_and_functions.potion --run
potionc examples/05_spawn_send_receive.potion
potionc demo/main.potion --outdir demo/target --no-beam
```

Package install:

```bash
# Generate .deb installer
bash packaging/packaging-potion-deb.sh

# Debian/Ubuntu
sudo apt install ./dist/potion-lang_0.1.0_all.deb

# Generate .rpm installer
bash packaging/packaging-potion-rpm.sh

# Fedora/RHEL
sudo dnf install ./dist/rpmbuild/RPMS/noarch/potion-lang-0.1.0-1.noarch.rpm
```

## Current Status

- Experimental and still evolving
- Breaking changes are possible while the syntax and compiler pipeline settle
- Type checking is intentionally lightweight
- Some practical capabilities currently rely on Erlang bridge modules instead of pure Potion
- Erlang interop exists today, but function existence and arity are not validated by the compiler

## Roadmap

- Done: typed `val`, typed `var`, typed parameters, `none`, maps, lists, `match`, `if`/`else`
- Done: concurrency primitives, semantic analysis, CLI compile/run flow, sibling-module imports
- In progress: broader language coverage, cleaner interop ergonomics, more complete static checks
- Still missing: atom literals, tuple syntax, richer module system, direct BEAM generation without Erlang as an intermediate step

## Documentation

- [`docs/language-spec.md`](./docs/language-spec.md): current implemented syntax and semantics
- [`docs/architecture.md`](./docs/architecture.md): lexer, parser, semantic analysis, codegen, and CLI pipeline
- [`README-pt-br.md`](./README-pt-br.md): Portuguese overview
- [`demo/README.md`](./demo/README.md): feature-server demo walkthrough
- [`examples/README.md`](./examples/README.md): language examples
- [`./.github/CONTRIBUTING.en.md`](./.github/CONTRIBUTING.en.md): contribution guide
- [`./.github/CODE_OF_CONDUCT.en.md`](./.github/CODE_OF_CONDUCT.en.md): code of conduct
