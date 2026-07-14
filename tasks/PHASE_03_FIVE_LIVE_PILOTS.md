# Phase 3 — Five Live Pilots（Gate 2）

## Goal

接入真实 Qianwen-Image-Edit、Geneval2、GPT teacher，完成五条可溯源轨迹。

## Cases

A direct success；B regenerate；C local edit；D non-monotonic branch recovery；E persistent failure/budget stop。

## Requirements

- API calls idempotent/resumable/cached；
- 每个 action request、raw output、canonical action、backend request、image、Geneval2、transition 全部落盘；
- 自动 pilot report；
- 对每轮分析好/不好及 alternative action；
- Gate 2 只审查五条轨迹是否足以支撑 SFT 设计。
