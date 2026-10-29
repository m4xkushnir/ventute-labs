# Ventute Labs

Standalone tooling for [Ventute](https://ventute.com), a business simulator. Nothing here talks to
Ventute's servers. Everything runs offline against the files in this repo.

## What's here

| Path | Contents |
|---|---|
| `schemas/` | JSON Schemas (draft 2020-12) for a starting scenario: `scenario` (the whole thing), `founding_data` and `charter` |
| `samples/` | 30 synthetic evaluation samples. Each folder has `facts.json` (what was true), `output.txt` (the report written from it) and `labels.json` (problems planted in the report, empty when clean) |
| `tools/make_samples.py` | The script that built `samples/`. Rerun it to rebuild them |

Label types in `samples/`: `numeric_mismatch`, `hallucination`, `contradiction`,
`internal_inconsistency`, `wrong_language`.

## Projects

Each project is a GitHub issue. Put each one in its own top-level folder (`generator/`, `evaluator/`)
with its own README and tests.

## Rules

- Use your own LLM API key from an environment variable. Never commit keys, `.env` files or real
  personal data.
- All changes go through a pull request into `main`.
- See `CONTRIBUTING.md` before your first pull request. Signing `CLA.md` is required.

## Ownership

Copyright © Maxim Cusnir (Ventute, P.IVA 04156050124). All rights reserved. This repository is not open source.
