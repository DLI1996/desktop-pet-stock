# Task Plan: Market Safety Overhaul

## Goal
Make desktop-pet-stock safer and more correct by fixing exchange-time handling, requiring opt-in for desktop side effects, rejecting unsafe quote data, and locking dependencies reproducibly.

## Next Step
Commit this approved plan, then complete Iteration 1 using the existing red timezone test.

## Current Phase
Phase 1

## Phases

### Phase 1: Plan and baseline
- [x] Capture the four implementation items and their order.
- [x] Record the existing test baseline: 11 tests pass before the timezone regression test.
- [x] Preserve the minimized red timezone test as the first feedback loop.
- [ ] Commit planning artifacts without committing the failing test.
- **Status:** in_progress

### Phase 2: Iteration 1 — exchange timezone correctness
- [ ] Diagnose with `TestMarketOpen.test_uses_exchange_timezone_for_aware_datetime`.
- [ ] Implement exchange-time normalization test-first.
- [ ] Run targeted and full tests; commit the change.
- [ ] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** pending

### Phase 3: Iteration 2 — opt-in desktop side effects
- [ ] Build a tight red loop proving browser/app/file actions are disabled by default.
- [ ] Diagnose the current policy boundary and implement an explicit config opt-in.
- [ ] Run targeted and full tests; commit the change.
- [ ] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** pending

### Phase 4: Iteration 3 — quote-data validation
- [ ] Build a tight red loop for non-finite, impossible, or internally inconsistent quote data.
- [ ] Diagnose each provider boundary and implement centralized validation.
- [ ] Run targeted and full tests; commit the change.
- [ ] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** pending

### Phase 5: Iteration 4 — reproducible dependency locking
- [ ] Build a red-capable reproducibility check for unconstrained dependency resolution.
- [ ] Diagnose the existing `requirements.txt` workflow and select a uv-compatible lock artifact.
- [ ] Generate and verify the lock workflow; commit the change.
- [ ] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** pending

### Phase 6: Final verification and delivery
- [ ] Run the full suite and repository checks from a clean working tree.
- [ ] Confirm all review findings are resolved or explicitly accepted.
- [ ] Summarize remaining privacy, provider-contract, holiday-calendar, and asset-license risks.
- **Status:** pending

## Iteration Contract

Every implementation phase uses the same gate:

1. `/diagnosing-bugs`: name and run one fast, deterministic, red-capable command; minimize the repro; rank and probe 3–5 falsifiable hypotheses.
2. `/implement`: keep the regression test red before the fix, make the smallest production change at the correct seam, run targeted tests regularly and the full suite once, then commit.
3. `/code-review`: use the pre-iteration commit as the fixed point and this plan as the spec; run Standards and Spec reviews in parallel sub-agents; fix material findings before advancing.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Work sequentially, one risk per commit and review | Keeps each diagnosis loop and review fixed point isolated. |
| Use this plan as the implementation spec | The user asked for a persistent plan and the requirements live here. |
| Treat privacy/provider contract and asset licensing as residual risks | They need provider/legal decisions, not safe unilateral code changes. |
| Keep the existing failing timezone test | It already satisfies the red-loop gate for Iteration 1. |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| Repository `.venv` is absent | Use `/Users/donaldli/.codex/.venv/bin/python` for stdlib-only tests; never install into system Python. |
| Patch replacement rejected delete+add of the same files | Replaced planning files with separate delete and add operations. |
| `git diff --cached --check` found trailing blank lines | Removed the blank lines before retrying the commit. |
