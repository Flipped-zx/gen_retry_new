# ADR-0001：统一使用 Qianwen-Image-Edit 后端

- Status: Superseded by ADR-0006
- Version: v0.2

This ADR is retained as the historical v0.2 decision. New episodes use the
accepted `qwen_dual_backend@1` execution profile defined by ADR-0006.

## Decision

v0.2 只使用一个底层 image executor：`Qianwen-Image-Edit`。

逻辑动作仍为：

```text
generate_image → backend generate/regenerate mode
edit_image     → backend edit mode with source image
```

## Rationale

- 用户现有环境已具备 Qianwen-Image-Edit 生成/编辑能力；
- 统一部署和缓存；
- 保留逻辑动作有利于 decision learning、source lineage、credit assignment 和 action ablation。

## Consequences

- adapter 名称固定为 `QianwenImageEditAdapter`；
- action schema 仍区分 generation/edit instruction；
- 所有文档、fixtures、reports 的 backend ID 统一为 `qianwen_image_edit`；
- image outputs are recorded through environment-owned artifact manifests, not
  as planner-predicted paths;
- 如未来增加第二后端，必须新 ADR，不得静默更改。
