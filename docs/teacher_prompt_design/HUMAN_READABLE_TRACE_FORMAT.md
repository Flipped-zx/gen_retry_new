# Human-Readable Trace Format

Date: 2026-07-15

Exporter: `src/gen_retry/cli/export_trajectory_trace.py`

## Goal

The trace should read like a GenSearcher/GenEvolve-style trajectory: each turn shows what the Teacher saw, what it emitted, what tool/environment did, what the verifier observed, and how memory/best-so-far changed.

Immutable audit events remain unchanged.

## Required Turn Sections

Each turn should show:

1. system prompt version/hash;
2. exact sanitized Teacher text input when persisted;
3. atomic constraints;
4. compact history table or summary;
5. latest/best state;
6. visible image references and labels;
7. retrieved full Skill or active compact operators;
8. raw redacted Teacher output;
9. canonical action;
10. instruction-quality result for image actions;
11. exact Qwen-Image-Edit input;
12. output image;
13. Geneval2 atom table;
14. fixed/regressed/persistent transition;
15. latest/best/budget update;
16. supervision assessment when labels are available.

## Current Exporter Behavior

The exporter now includes:

- system prompt version/hash;
- teacher input block;
- image labels and latest/best equality;
- active compact operators;
- raw redacted Teacher output;
- instruction-quality result;
- exact Qwen input block;
- image artifact and Geneval2 atom table;
- transition and best-so-far update.

For historical runs that did not persist `teacher_text_input`, the exporter emits a sanitized reconstruction from artifacts instead of claiming exact input.

## Tests

Mock trace-format tests are in:

- `tests/unit/test_export_trajectory_trace_format.py`
