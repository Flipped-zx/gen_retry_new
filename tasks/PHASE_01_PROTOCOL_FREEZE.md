# Phase 1 — Protocol Freeze（Gate 1）

## Goal

冻结最小协议并通过 mock contract tests。

## Implement

- TaskSpec schema；
- Action protocol v0.2；
- Episode event schema；
- Planner view schema；
- IDs/artifact manifest；
- parser/validator；
- invalid-action observations；
- schema fixtures and contract tests。

## Do not implement

- live Qianwen-Image-Edit；
- live Geneval2；
- GPT teacher；
- SFT exporter。

## Gate 1 review

只审查 ownership、action minimality、backend semantics、replay completeness。使用 `SOL_REVIEW_REQUEST`，最多三个问题。
