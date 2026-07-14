# ADR-0002：Event-sourced Canonical Memory

- Status: Accepted

## Decision

Persistent Memory 由不可变事件和确定性 reducer 构建。Planner raw response 不进入 Memory。

## Rationale

保证每个 action 输入、原始输出、validated action、tool execution、Geneval2 result、transition、branch 和 submit 均可追溯和 replay。
