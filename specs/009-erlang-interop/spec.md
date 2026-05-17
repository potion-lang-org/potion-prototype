# Erlang interop

## Status

Partially implemented

## Goal

Allow Potion programs to call existing Erlang modules explicitly, while avoiding the claim that Erlang bridge helpers are Potion's standard library.

## User-facing syntax

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

## Invalid examples

```potion
fn main() {
    val response = httpc.request("https://example.com")
}
```

The Erlang module must be imported before use.

## Semantics

`import erlang <module>` makes an Erlang module available for explicit external calls. Calls use Potion syntax `<module>.<function>(args...)`. Results are dynamic from Potion's current type-checking perspective.

## Current implementation notes

The parser creates external module call nodes for `module.function(...)`. The semantic analyzer validates only that `module` was imported with `import erlang`. Codegen emits `module:function(...)`.

## Guardrails

- The compiler does not validate that the Erlang module exists.
- The compiler does not validate that the function exists.
- The compiler does not validate Erlang function arity.
- Erlang bridge modules used by demos are support code for the POC, not Potion standard library design.
- Missing tuple, binary, and fun syntax still limits ergonomic Erlang API usage today.

## Acceptance examples

```potion
import erlang httpc

fn main() {
    val response = httpc.request("https://example.com")
    print(response)
}
```

Expected current Erlang shape:

```erlang
Response = httpc:request("https://example.com"),
io:format("~p~n", [Response])
```
