# Phase 2 — Mock Replay Runtime

## Goal

无外部 API 地完成 deterministic multi-round episode。

## Implement

- append-only event store；
- state reducer；
- transition builder；
- best-so-far selection；
- compact planner view；
- fake Qianwen-Image-Edit executor；
- fake Geneval2 adapter；
- five mock fixtures；
- replay determinism and provenance tests。

## Exit criteria

同一个 events.jsonl 从头 replay 产生字节等价 canonical state；branch from historical attempt 可正确重建。
