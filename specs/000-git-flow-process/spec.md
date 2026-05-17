# Git Flow process

## Status

Planned

## Goal

Define how Potion should use branches, pull requests, and specs so language evolution is spec-driven and release-oriented.

Specs are the source of truth for language evolution. Every language feature must start with a spec, and implementation work must keep the corresponding spec updated in the same branch.

## User-facing syntax

This process spec has no Potion syntax. The user-facing workflow is Git branch and PR naming:

```text
main
develop
feature/014-tuples
feature/015-atoms
feature/016-binary-pattern-matching
fix/parser-error-message
release/0.2.0
hotfix/0.2.1
```

## Invalid examples

```text
main <- direct commit
main <- feature/014-tuples
develop <- direct commit
feature/014-tuples without specs/014-tuples/spec.md
```

Implementation PRs without a matching spec are invalid for language features.

## Semantics

Potion follows a Git Flow-inspired process:

- `main` is stable and represents publishable versions.
- `main` must not receive direct commits.
- `main` only receives merges from `release/*` or `hotfix/*`.
- `develop` is the main integration branch.
- every feature starts from `develop`.
- `develop` only receives changes through PRs.
- `feature/<number>-<short-name>` is used for new language features.
- `fix/<short-name>` is used for non-emergency fixes.
- `release/<version>` prepares publishable versions.
- `hotfix/<version-or-name>` starts from `main` for urgent fixes.

Each language feature PR must include:

- the created or updated spec.
- valid Potion examples.
- acceptance criteria.
- tests or fixtures when applicable.
- compatibility notes.
- known limitations.

Feature status must use only these labels: `Implemented`, `Partially implemented`, `Planned`, `Experimental`, or `POC workaround`.

Releases must create semantic version tags such as:

```text
v0.1.0
v0.2.0
v0.3.0
```

## Current implementation notes

The repository currently has SDD specs under `specs/`. This process document defines the intended project workflow, but branch protections, required PR checks, release automation, and tag automation are not enforced by code in this repository.

The current SDD set documents the existing Potion prototype and its Erlang backend as the current implementation, not as final language constraints.

## Guardrails

- Do not implement a language feature without a corresponding spec.
- Do not document POC workarounds as final language design.
- Do not treat current compiler limitations as permanent choices.
- Do not treat Erlang bridge helpers as Potion's definitive standard library.
- Do not treat Erlang code generation as the mandatory final backend.
- Do not merge feature branches directly into `main`.
- Do not use release branches for feature development.
- Do not mark incomplete features as `Implemented`.

## Acceptance examples

Tuple feature workflow:

```text
develop
  -> feature/014-tuples
      -> specs/014-tuples/spec.md
      -> examples for tuple syntax
      -> parser/codegen/semantic tests when implementation starts
  -> PR back to develop
```

Release workflow:

```text
develop
  -> release/0.2.0
  -> PR or merge to main
  -> tag v0.2.0
  -> merge release changes back to develop
```

Hotfix workflow:

```text
main
  -> hotfix/0.2.1
  -> PR or merge to main
  -> tag v0.2.1
  -> merge hotfix changes back to develop
```
