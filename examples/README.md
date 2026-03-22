# Potion Examples

This directory contains small `.potion` programs that demonstrate the language features currently implemented in the compiler.

Files:

- `01_values_and_functions.potion` - global values, local values, typed declarations, function calls, arithmetic and printing.
- `02_var_and_none.potion` - `var` declarations and the `none` literal.
- `03_conditionals_and_comparisons.potion` - boolean comparisons with `if` / `else`.
- `04_maps_and_match.potion` - map literals and pattern matching.
- `05_spawn_send_receive.potion` - process spawning, message sending and receiving.
- `06_end_to_end_features.potion` - a compact end-to-end example combining several language features.
- `07_var_reassignment.potion` - sequential local reassignment with `var`.
- `08_var_reassignment_control_flow.potion` - `var` reassignment across `if` and `match` branches.
- `09_type_error_string_plus_int.potion` - intentionally invalid example showing compile-time rejection of `str + int`; use `to_string(...)` instead.
