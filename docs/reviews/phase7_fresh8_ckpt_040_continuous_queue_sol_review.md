# Phase 7 Checkpoint 40 And Continuous Queue Sol Review

## Final Verdict

`PASS_CONTINUE_QUEUE`

No checkpoint-40 data-validity, evaluator, SFT-boundary, or wrong-direction
blocker remains. Start the continuous global queue for episodes 51-200 after
41-50 completes.

## Backend Contract Resolution

The initial response returned `STOP_BLOCKING` because the minimum evidence
packet omitted the accepted ADR authorizing the dual backend. The same reviewer
re-reviewed after receiving:

- `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`;
- `docs/architecture/MODULE_CONTRACTS.md`, section 6;
- `README_START_HERE.md`.

ADR-0006 is accepted, explicitly supersedes ADR-0001, and defines
`qwen_dual_backend@1`:

```text
generate_image -> Qwen-Image-2512
edit_image     -> Qwen-Image-Edit-2511
```

This satisfies the explicit ADR exception in `AGENTS.md`. The checkpoint's
backend provenance conforms to the governing contract.

## Checkpoint Decision

- Range 21-40 materially improved atom pass, AM, and GM over first attempts.
- Lower all-pass rate and increased regression/ineffective-action exposure are
  acceptable difficult-prompt evidence.
- Harmful, ineffective, rejected, and tool-response records remain excluded
  from positive SFT loss.
- No prospective policy correction is required before continuing.

## Approved Scheduler

- One global pending queue for episodes 51-200.
- Sixteen logical workers: two per physical HCU.
- Eight Teacher slots and eight physical-HCU execution slots.
- Existing lock ordering and per-episode causal sequencing.
- Asynchronous 20-episode audits and 50-episode deep reviews.
- Scheduler profile provenance at every launch/retry boundary.

## Required Stop And Retry Semantics

- Persist an admission-stop flag and check it atomically before every episode
  claim and after every completed or failed child.
- Once stopped, do not claim another pending episode. Active episodes may
  finish, or stop only after durable events, artifacts, hashes, and manifests.
- Derive pending work from canonical reduced events. Skip only a valid terminal
  submission.
- Resume under scheduler and episode locks from the last committed event.
- Verify cached image decode, dimensions, and hash before reuse.
- Reject execution-profile mismatch.
- Defer failed unsubmitted episodes until the initial queue drains, then retry
  only pending episodes within five orchestration passes.
- Preserve prompts, models, seeds, score/evaluator semantics, concurrency
  limits, and profile provenance.

