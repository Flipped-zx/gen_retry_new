# ADR-0003：不设置独立 refine_prompt 动作

- Status: Accepted

## Decision

每个 `generate_image` / `edit_image` action 自带可执行 instruction。

## Rationale

“refine prompt”属于 action 参数构造，而非独立环境动作。单独拆分会增加回合数、schema 和信用分配歧义。
