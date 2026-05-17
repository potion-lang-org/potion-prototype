# Receive on

## Status

Partially implemented

## Goal

Define Potion's message receive syntax for process communication while separating the intended message contract from the current map-based POC shape.

## User-facing syntax

```potion
fn worker() {
    receive {
        on hello(name, caller) {
            print("Hello, " + name)
            send(caller, {ok: "received"})
        }

        on any {
            print("unexpected")
        }
    }
}
```

With a guard:

```potion
receive {
    on data(value, caller) when value > 10 {
        send(caller, {ok: value})
    }
}
```

## Invalid examples

```potion
receive {
    on data(value, caller, extra) {
        print(value)
    }
}
```

The current implementation supports only the primary payload binding plus the `reply_to` convention.

## Semantics

`receive` waits for a message and runs the first matching `on` clause. `on <tag>(...)` matches a tagged message. `on any` is the fallback clause. Optional `when` guards refine a clause and must evaluate to a boolean.

The first binding represents the payload associated with the tag. Extra bindings represent named message fields by convention; today only `reply_to` is recognized.

## Current implementation notes

Messages are currently represented as Erlang maps. `on hello(name, caller)` compiles to a map pattern for `#{hello := Name, reply_to := Caller}`. `send(target, message)` compiles to Erlang `!`. `sp worker()` compiles to `spawn(fun () -> worker() end)`. `self()` returns the current process id.

## Guardrails

- The current map shape is a POC convention, not the final message representation.
- `reply_to` is not a reserved Potion keyword.
- The two-binding limit is temporary.
- There are no OTP abstractions such as supervisors or GenServer-style behavior in Potion today.

## Acceptance examples

```potion
fn main() {
    val pid: pid = sp worker()
    send(pid, {hello: "Bruce", reply_to: self()})
}
```

Expected current Erlang shape:

```erlang
Pid = spawn(fun () -> worker() end),
Pid ! #{hello => "Bruce", reply_to => self()}
```
