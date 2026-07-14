# ADR-0004: Develop v3 in a new clean-room repository

## Status

Accepted.

## Decision

Gen-Retry v3 is developed in a new Git repository. Legacy Gen-Retry and external reference repositories are configured as read-only source roots.

## Rationale

- avoids collisions with old schemas, prompts, artifacts, and exporters;
- prevents accidental reuse of raw assistant JSON and legacy stage-specific targets;
- supports deterministic provenance for every adapted component;
- allows selective reuse backed by path, commit, symbol, and license evidence;
- reduces rollback and experiment contamination risk.

## Consequences

- Phase 0 becomes external repository archaeology rather than in-place archaeology;
- no production imports or editable installs may point to the legacy repository;
- reusable logic is reimplemented or copied into v3 only after Protocol Freeze and license review;
- external paths are local configuration and are never committed with machine-specific values.
