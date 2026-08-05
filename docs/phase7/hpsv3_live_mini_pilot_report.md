# HPSv3 Live Mini-Pilot

## What Was Run

The completed 1k Flow-DPPO run is the baseline arm. A fresh HPS-aware arm was
started from the exact same TaskSpec and original prompt for
`phase3_ep_926`; the original 1k trajectory was not modified. The live loop
was:

`Qwen image -> Geneval2 -> HPSv3 -> PlannerContext v0.8 -> Teacher Action`

HPS was scored in its isolated official venv with the local
`Qwen2-VL-7B-Instruct` backbone. The HPS event was appended before every next
v0.8 PlannerContext, and the canonical trajectory passed validation.

Pairing was checked by hashing both arms' imported `task_spec.json` and the
original prompt. Both hashes match: task spec
`670ab482272404de9a185f28ed8b10f763dec9dbe94a1078392b3c3c5423ef61`, prompt
`e7a5b42d40148ea0a9cae266ee50d99328d6d71d0023d8782664b1f47222237a`.

Only one episode was allowed to complete because one five-attempt trajectory
consumed about 38 minutes on the available HCU. The remaining five directories
were prepared as fresh scaffolds; their image generation was stopped before
the first image and they are not included in any result.

## Completed Pair

| Arm / attempt | Geneval2 passed atoms | Geneval2 GM | HPSv3 mu |
| --- | ---: | ---: | ---: |
| Existing 1k baseline `a_002` (submitted) | 7/8 | 0.066457 | 7.101077 |
| Fresh HPS arm `a_003` (submitted) | 7/8 | 0.095201 | 3.808064 |

The HPS arm tied the primary pass-count objective and had a higher Geneval2
GM tie-break, but its submitted HPS score was substantially lower than the
existing baseline child. This single pair therefore does **not** show quality
mitigation.

## HPS Decision Trace

| Attempt | Geneval2 passed | HPS mu | Delta from source | Risk |
| --- | ---: | ---: | ---: | --- |
| `a_000` | 6/8 | 4.486021 | n/a | unknown |
| `a_001` | 5/8 | 2.039250 | -2.446771 | high |
| `a_002` | 6/8 | 3.921850 | -0.564171 | watch |
| `a_003` | 7/8 | 3.808064 | -0.677957 | watch |
| `a_004` | 6/8 | 2.259906 | -1.548158 | high |

After the first high-risk edit, the Teacher performed a real
`query_skill(local_edit_preservation)` followed by `skill_returned`, then
continued with a local edit. HPS remained advisory: it did not veto a semantic
repair, and the reducer still selected/submitted the Geneval2 best attempt
`a_003`.

## Conclusion

This is the first actual image-level proof that the HPS field wiring works in
the live loop. It is not evidence that HPS improves image quality. In this
pair, HPS changed the retry path and preserved Geneval2 pass-count behavior,
but the final HPS score remained below the existing 1k baseline. A multi-pair
fresh rerun is still required before making any claim about mitigation.
