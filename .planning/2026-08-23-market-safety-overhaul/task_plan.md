# Task Plan: Market Safety Overhaul

## Goal
Make desktop-pet-stock safer and more correct by fixing exchange-time handling, requiring opt-in for desktop side effects, rejecting unsafe quote data, locking dependencies reproducibly, and reducing the remaining operational risks.

## Next Step
Implement frontier issue #2 first to produce the runnable US/VIX demo; issue #5 is independently ready, while issues #3 and #4 remain blocked by #2.

## Current Phase
Phase 11

## Phases

### Phase 1: Plan and baseline
- [x] Capture the four implementation items and their order.
- [x] Record the existing test baseline: 11 tests pass before the timezone regression test.
- [x] Preserve the minimized red timezone test as the first feedback loop.
- [x] Commit planning artifacts without committing the failing test.
- **Status:** complete

### Phase 2: Iteration 1 — exchange timezone correctness
- [x] Diagnose with `TestMarketOpen.test_uses_exchange_timezone_for_aware_datetime`.
- [x] Implement exchange-time normalization test-first.
- [x] Run targeted and full tests; commit the change.
- [x] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** complete

### Phase 3: Iteration 2 — opt-in desktop side effects
- [x] Build a tight red loop proving browser/app/file actions are disabled by default.
- [x] Diagnose the current policy boundary and implement an explicit config opt-in.
- [x] Run targeted and full tests; commit the change.
- [x] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** complete

### Phase 4: Iteration 3 — quote-data validation
- [x] Build a tight red loop for non-finite, impossible, or internally inconsistent quote data.
- [x] Diagnose each provider boundary and implement centralized validation.
- [x] Run targeted and full tests; commit the change.
- [x] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** complete

### Phase 5: Iteration 4 — reproducible dependency locking
- [x] Build a red-capable reproducibility check for unconstrained dependency resolution.
- [x] Diagnose the existing `requirements.txt` workflow and select a uv-compatible lock artifact.
- [x] Generate and verify the lock workflow; commit the change.
- [x] Review the iteration against its pre-iteration commit on Standards and Spec axes.
- **Status:** complete

### Phase 6: Final verification and delivery
- [x] Run the full suite and repository checks from a clean working tree.
- [x] Confirm all review findings are resolved or explicitly accepted.
- [x] Summarize remaining privacy, provider-contract, holiday-calendar, and asset-license risks.
- **Status:** complete

### Phase 7: Iteration 5 — configuration resilience
- [x] Build a tight red loop for malformed or wrong-typed user configuration.
- [x] Diagnose the configuration boundary and safely recover to defaults.
- [x] Run targeted and full tests; commit and two-axis review.
- **Status:** complete

### Phase 8: Iteration 6 — quote-provider privacy
- [x] Build a tight red loop proving HTTP fallback cannot send a watched symbol without explicit opt-in.
- [x] Diagnose the provider fallback boundary and make direct HTTP explicitly opt-in.
- [x] Run targeted and full tests.
- [x] Commit and two-axis review.
- **Status:** complete

### Phase 9: Iteration 7 — VIX desktop interaction smoke test
- [x] Build a deterministic offscreen red loop for the hover menu and VIX detail states.
- [x] Add the one-item metrics menu and Cboe daily-history detail view.
- [x] Run the focused smoke check and full suite, preserving source/date/loading/failure behavior.
- [x] Resolve review findings by separating the provider, covering parser edge cases, and excluding unrelated tooling files.
- **Status:** complete

### Phase 10: External governance decisions
- [ ] Record the provider-contract decision required for any direct Sina use.
- [ ] Record the asset-license decision required before redistribution or commercial use.
- [ ] Record the signing/distribution policy if the app is distributed outside local development.
- **Status:** pending (requires provider, rights-holder, or release-owner authority)

### Phase 11: China / US market switch
- [x] Run `grill-with-docs` to settle the switch behavior and boundaries, then synthesize the result with `to-spec`.
- [x] Remove the automatic VIX hover menu so the original 350 ms quote-card interaction is visible again.
- [x] Test the original China quote connection and inspect how its data maps to the existing card before deciding the remaining menu behavior.
- [x] Replace the original mini quote card and native hover `QMenu` with one compact macOS-style hover market panel; use the supplied image as visual direction, not as a requirement for its extra metrics or Level 2 features.
- [x] Start the packaged app automatically at macOS login, retain single-instance behavior, and initialize each app session in the US Market view without changing the configured Watched instrument.
- [x] Use `中国 / 美国` switch buttons in the market panel rather than a mixed list.
- [x] Lay out each list row with its name left-aligned and current value right-aligned; preload the current view's summaries together behind a list-wide wireframe, without constructing detail charts.
- [x] Keep the active market row visibly highlighted, including after returning from its detail view.
- [ ] Reserve a `＋ 添加指标` footer affordance; its behavior is deferred.
- [x] Replace the list with detail inside the same market panel and use `返回`; do not open a separate OS window.
- [x] Activating a China row selects it as the watched instrument and opens detail; VIX opens detail without changing the watched instrument.
- [x] Treat future US equity indices such as S&P 500 and Nasdaq as watched instruments: selecting one replaces the current China instrument and drives the existing market reaction.
- [ ] Preserve the existing `FLAT / RISE / SURGE / FALL` market-reaction logic and its animation/effect behavior when the watched China instrument changes; panel/detail state must not introduce a second reaction model.
- [x] Keep VIX out of the animation state machine: it never changes or overrides `FLAT / RISE / SURGE / FALL` and only shows one independent high-volatility alert overlay.
- [x] When the VIX alert is active, keep a small badge visible beside the pet even while the market panel is closed; clicking it opens VIX detail directly.
- [x] Keep the panel open while the pointer is over either the pet or panel; after leaving both, close it after about 200ms. On the next hover, reopen the list while preserving the last Market view and Active row.
- [ ] Validate the proposed alert rule (`VIX close >= 30`; clear after two closes `< 25`) with a deterministic historical frequency replay before implementation.
- [x] In detail, show latest value/change, high, low, open, previous close, data source, and an inspectable line where pointing reveals the exact time and value.
- [x] Load a row's historical Detail series only after activation; show its own loading wireframe, reveal the hovered point after 350ms, and dismiss the point tooltip about 200ms after leaving.
- [ ] After the frontend contract is confirmed, research which backend sources can supply the required China and VIX historical granularity without weakening the existing privacy/provider constraints.
- [ ] Fix the observed `爆拉！` regression test-first: choosing another index must exit the forced surge/demo state and show the selected index normally.
- [x] Publish the synthesized Chinese specification as GitHub issue #1 with `ready-for-agent`.
- [x] Publish four approved tracer-bullet tickets from issue #1: #2 US/VIX demo, #3 China view, #4 VIX alert, and #5 macOS login launch.
- [x] Run `implement` for the resulting ticket(s), including TDD and two-axis code review.
- **Status:** in_progress

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
| PySide6 is unavailable in the lightweight test venv | Prepare the documented repository `.venv` and use an offscreen UI harness for the real path. |
| `uv venv` could not write its default cache | Retry with task-scoped `UV_CACHE_DIR=/private/tmp/desktop-pet-stock-uv-cache`. |
| `uv venv` then could not write its managed-Python directory | Also set task-scoped `UV_PYTHON_INSTALL_DIR=/private/tmp/desktop-pet-stock-uv-python`. |
| Managed Python download failed in the restricted network sandbox | Retry the same resolved command with approved network access. |
| Combined product/planning patch missed one context line | Split product changes from planning updates and reapplied against current text. |
| Iteration 4 review found launcher hash enforcement missing | Added `--require-hashes` to both Finder launcher install paths, re-verified, and re-reviewed. |
| Phase 9 worktree initially opened at stale Phase 3 commit | Switched the detached worktree to existing Phase 9 commit `41d7db5`. |
| Phase 9 worktree switch was sandbox-blocked by Git metadata permissions | Re-ran the resolved detached switch with approved access. |
