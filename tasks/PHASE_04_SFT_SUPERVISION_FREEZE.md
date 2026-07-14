# Phase 4 — SFT Supervision Freeze（Gate 3）

## Goal

根据五条 Pilot 冻结训练消息、mask 和样本选择。

## Decide

- system prompt；
- multimodal user/tool observation layout；
- exact assistant action target；
- harmful action/history/recovery policy；
- query_skill supervision；
- image/history compression；
- token budget；
- prompt-group split；
- initial action / edit / regenerate / recovery / submit 配比。

## Exit criteria

对每个 target token 的来源和 loss mask 可解释；train/inference message renderer 共用同一协议代码。
