# v0.7 / PlannerContext v0.6 五条配对轨迹分析

## 汇总

- 配对轨迹：5
- 首次生成 atom pass：34 -> 35 (+1)
- 最终提交 atom pass：39 -> 40 (+1)
- 首次生成平均 GM：17.41 -> 7.81 (-9.60)
- 最终提交平均 GM：19.70 -> 18.32 (-1.38)
- 最终提交平均 AM：77.68 -> 77.33 (-0.35)
- 旧方案自身 retry atom gain：+5
- 新方案自身 retry atom gain：+5
- 旧方案自身 retry GM gain：+2.30
- 新方案自身 retry GM gain：+10.51
- 配对结果：{'negative_fewer_atoms': 1, 'positive_equal_atoms_higher_gm': 2, 'positive_more_atoms': 2}
- GM tie-break 实际更新 best：6 次
- GM 更高但 pass 更少、被策略正确拒绝：2 次
- 回到历史 source 再编辑：4 次
- 首次生成后主动重新 generate：2 次

## 逐条

| Episode | 旧提交 pass | 新提交 pass | Δpass | 旧 GM | 新 GM | ΔGM | 结论 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| phase3_ep_001 | 8 | 8 | +0 | 5.28 | 8.77 | +3.49 | positive_equal_atoms_higher_gm |
| phase3_ep_008 | 9 | 9 | +0 | 8.08 | 22.80 | +14.72 | positive_equal_atoms_higher_gm |
| phase3_ep_010 | 8 | 9 | +1 | 3.34 | 7.39 | +4.05 | positive_more_atoms |
| phase3_ep_012 | 9 | 10 | +1 | 10.70 | 42.69 | +31.98 | positive_more_atoms |
| phase3_ep_020 | 5 | 4 | -1 | 71.11 | 9.94 | -61.17 | negative_fewer_atoms |

## 新轨迹逐 Attempt 行为

### `phase3_ep_001`

| Attempt | Action | Source | Backend | Pass | GM | Fixed | Regressed | Best |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| a_000 | generate_image | - | qwen_image | 7 | 0.87 | - | - | yes |
| a_001 | edit_image | a_000 | qianwen_image_edit | 8 | 3.44 | c_001 | - | yes |
| a_002 | edit_image | a_001 | qianwen_image_edit | 8 | 5.80 | - | - | yes |
| a_003 | edit_image | a_002 | qianwen_image_edit | 8 | 6.58 | - | - | yes |
| a_004 | edit_image | a_003 | qianwen_image_edit | 8 | 8.77 | - | - | yes |

### `phase3_ep_008`

| Attempt | Action | Source | Backend | Pass | GM | Fixed | Regressed | Best |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| a_000 | generate_image | - | qwen_image | 8 | 22.34 | - | - | yes |
| a_001 | edit_image | a_000 | qianwen_image_edit | 9 | 22.80 | c_002 | - | yes |
| a_002 | edit_image | a_001 | qianwen_image_edit | 8 | 26.16 | - | c_001 | no |
| a_003 | edit_image | a_001 | qianwen_image_edit | 8 | 25.58 | - | c_001 | no |
| a_004 | edit_image | a_001 | qianwen_image_edit | 8 | 12.09 | - | c_001 | no |

### `phase3_ep_010`

| Attempt | Action | Source | Backend | Pass | GM | Fixed | Regressed | Best |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| a_000 | generate_image | - | qwen_image | 7 | 0.89 | - | - | yes |
| a_001 | edit_image | a_000 | qianwen_image_edit | 8 | 4.72 | c_006 | - | yes |
| a_002 | edit_image | a_001 | qianwen_image_edit | 9 | 7.39 | c_003 | - | yes |
| a_003 | edit_image | a_002 | qianwen_image_edit | 8 | 2.64 | - | c_003 | no |
| a_004 | edit_image | a_002 | qianwen_image_edit | 8 | 5.29 | - | c_003 | no |

### `phase3_ep_012`

| Attempt | Action | Source | Backend | Pass | GM | Fixed | Regressed | Best |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| a_000 | generate_image | - | qwen_image | 9 | 8.00 | - | - | yes |
| a_001 | edit_image | a_000 | qianwen_image_edit | 9 | 5.94 | - | - | no |
| a_002 | generate_image | - | qwen_image | 9 | 19.01 | - | - | yes |
| a_003 | edit_image | a_002 | qianwen_image_edit | 10 | 42.69 | c_010 | - | yes |
| a_004 | edit_image | a_003 | qianwen_image_edit | 9 | 24.59 | - | c_010 | no |

### `phase3_ep_020`

| Attempt | Action | Source | Backend | Pass | GM | Fixed | Regressed | Best |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| a_000 | generate_image | - | qwen_image | 4 | 6.95 | - | - | yes |
| a_001 | edit_image | a_000 | qianwen_image_edit | 4 | 7.38 | - | - | yes |
| a_002 | edit_image | a_001 | qianwen_image_edit | 1 | 0.00 | - | c_004, c_005, c_006 | no |
| a_003 | edit_image | a_001 | qianwen_image_edit | 4 | 6.22 | - | - | no |
| a_004 | generate_image | - | qwen_image | 4 | 9.94 | - | - | yes |


## 解释边界

The paired result measures the integrated system change. It does not isolate renderer routing, score feedback, Teacher prompt version, or stochastic generation.

因此本报告可以判断整套新方案是否方向正向，但不能单独把收益归因于 Qwen-Image、GM feedback、PlannerContext v0.6 或 Teacher prompt。要拆分因果贡献，仍需运行已准备的 edit-only v0.6 对照或固定 Action replay。
