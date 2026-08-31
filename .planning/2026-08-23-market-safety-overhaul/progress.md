# Progress Log

## Session: 2026-08-23

### Current Status
- **Phase:** 11 — China / US Market panel specification
- **Status:** specification published; implementation pending

### Actions Taken
- Created isolated plan `2026-08-23-market-safety-overhaul` and made it active.
- Recorded four sequential diagnose → implement → review iterations.
- Preserved the minimized timezone regression test in the working tree.
- Committed the persistent plan as `efa2d73`.
- Completed diagnosis: timezone normalization is the cause; session ranges and weekday handling are not.
- Implemented explicit `Asia/Shanghai` normalization for current and aware datetimes.
- Re-ran the minimized repro, provider tests, and full suite successfully.
- Committed Iteration 1 as `bd8c39c`.
- Ran parallel Standards and Spec reviews against `efa2d73`; both reported no findings.
- Confirmed Iteration 2 lacks a pure policy seam and PySide6 is unavailable in the lightweight test venv.
- Created the repository `.venv` and installed declared dependencies with task-scoped uv storage.
- Built a minimized offscreen UI test; it reproduced an unwanted Douyin launch in 4 ms twice.
- Proved `_auto_action()` ignores missing, false, and true configs, then added a default-false gate and explicit-enabled test.
- Verified the safety test file and full offscreen suite after the fix.
- Ran the Iteration 2 two-axis review against `bd8c39c`; both axes reported zero findings.
- Reproduced unsafe `NaN`, zero, and inconsistent quote data becoming successful results.
- Added one central quote-data guard at the `StockDataProvider` handoff and verified the targeted quote tests and full offscreen suite.
- Ran the Iteration 3 two-axis review against `9ab31f3`; both axes reported zero findings.
- Confirmed the three lower bounds fail a no-range lock check, then generated a 10-package hash-locked `requirements.txt` from `requirements.in`.
- Verified an offline hash-checked install and the full offscreen suite.
- Re-reviewed Iteration 4 after adding hash enforcement to both Finder launcher scripts; Standards and Spec both reported zero findings.
- Ran final clean-tree verification: exact-pin check, offline hash-checked install, `git diff --check`, and the full offscreen suite.
- User extended the safety scope to configuration resilience, direct-provider privacy, exchange closure handling, and the external governance decisions that code alone cannot make.
- Reproduced malformed user configuration aborting startup, added default/per-field validation at `load_config()`, and passed the full 17-test suite.
- Review found invalid UTF-8 and non-finite thresholds; added both regression cases, passed 18 tests, and re-review reported zero findings on both axes.
- Built and ran Phase 8's minimized privacy test twice; both runs prove one direct HTTP call occurs without consent. Caller tracing confirmed the unconditional provider fallback as the root cause.
- Implemented `enable_http_fallback`, default false, at the provider boundary; wired it from `PetWindow`, documented the privacy behavior, and added explicit-opt-in coverage.
- Ran the focused quote-provider/config tests, Python compilation, and the full offscreen suite successfully. The Phase 8 commit and two-axis review remain pending.
- Committed Phase 8 as `7541cf1`; review found one missing return annotation and stale connector documentation.
- Corrected both findings in `e9c90e2`, including a second stale fallback claim; re-review reported zero Standards and zero Spec findings, with 20 tests passing.
- Recovered this worktree from stale Phase 3 commit `9ab31f3` to Phase 9 baseline `41d7db5`; no tracked local changes were overwritten.
- Re-scoped Phase 9 to the delegated VIX smoke slice and selected the existing hover timer, `QMenu`, `QPainter`, and `urllib.request` seams.
- Added a deterministic three-row Cboe-format CSV fixture and captured the expected red result: no metrics menu appeared after the existing 350 ms hover delay.
- Added a one-action `VIX` hover menu and a painted detail view with the latest close, observation date, Cboe source, recent-close line, loading state, and failure state.
- Verified the focused smoke check, all 21 offscreen tests, Python compilation, and `git diff --check`.
- Addressed Phase 9 review: moved Cboe fetching/parsing to `vix_provider.py`, added deterministic parser edge-case tests, and precisely ignored unrelated `.agents/` and `skills-lock.json` without deleting them.
- Verified the review fixes: 2 parser tests and 3 combined VIX tests passed; all 23 offscreen tests, `compileall`, and `git diff --check` passed.
- Re-review found the tracked ignore policy out of scope; reverted only those two `.gitignore` lines and moved them to this checkout's local Git exclude while preserving both files.
- Began a China/US market-switch extension, then withdrew it before completion per user direction; no switch changes are retained.
- Added a persistent Phase 11 todo: `grill-with-docs` → optional `to-spec`/`to-tickets` for multi-session work → `implement` with TDD and code review.
- Started `grill-with-docs` for Phase 11, combining the grilling decision tree with inline domain-modeling documentation.
- Resolved the first Phase 11 design branch from the live UI: the market choice filters the watched-instrument catalog; VIX remains an independent metric. Created `CONTEXT.md` with the canonical terms.
- Grill round decision: chose native nested China and US market catalogs instead of a stateful switch.
- Grill round decision: limited the first US catalog to VIX only.
- Paused the remaining grill questions for a quick product spike, replaced the VIX hover smoke assertion with the original behavior contract, and captured the expected red result: the quote card appeared but one `VIX` menu was still visible.
- Removed only the automatic VIX hover wiring; the existing 350 ms timer now shows the original quote card without opening any menu. Focused smoke and all 23 offscreen tests pass.
- Clarified that `zn` meant the app's original China market quotes, reproduced “行情走丢了” twice with the production provider, and isolated the cause to a missing bridge file plus the default-disabled HTTP fallback.
- Verified an explicit Sina opt-in returns `sh000001` (`3912.52`, `+0.59%`, closed-market data), then launched the app with that opt-in for this session only; the repository's safe default remains unchanged.
- User confirmed several original China-market smoke paths work and reported one deferred bug: selecting another index after `爆拉！` leaves the forced surge/demo state active. Added an unchecked test-first plan item; no diagnosis or product code change was made.
- User supplied a macOS-style hover-panel reference and explicitly allowed replacing the original quote-card/menu UI. Recorded the reference as visual direction while keeping its unrequested Level 2 and multi-metric features out of scope.
- Grill decision: the replacement market panel uses `中国 / 美国` switch buttons and never mixes both markets in one list.
- Revised the interactive frontend mockup with persistent row highlighting, a deferred `＋ 添加指标` affordance, same-panel list/detail navigation, OHLC/previous-close/source fields, and an inspectable time/value line. No backend assumptions or product code changes were made.
- User confirmed same-panel detail navigation and required the original market reaction behavior to remain authoritative. Updated the mockup so China rows demonstrate `FLAT / RISE / SURGE / FALL` changes while VIX leaves the pet's watched China instrument and reaction unchanged.
- Confirmed future US equity indices replace the current watched instrument and drive the existing reaction model. Submitted the approved VIX PANIC brief once through Perplexity's standard Search mode, preserved the result URL, and recorded its fixed-threshold recommendation as research rather than an adopted product rule.
- Confirmed a VIX treatment may temporarily override the visible animation while the watched instrument keeps updating underneath. Ran a second Perplexity ordinary Search on what VIX should truthfully affect; it recommended a volatility/uncertainty overlay rather than a fifth directional state. Preserved the result URL.
- Discovered Perplexity's composer had retained Deep Research despite the requested normal search, explicitly switched the visible mode to Search before submitting, and updated the local ask-perplexity skill through a Luna medium subagent so ordinary Search is now the documented default.
- Grill decision: VIX will not change or override the pet animation. Reduced the proposed behavior to one independent high-volatility alert overlay; threshold validation remains a later deterministic data check.
- Grill decision: while active, the VIX high-volatility alert remains as a small badge beside the pet even with the market panel closed, and clicking it opens VIX detail directly.
- Grill decision: the panel stays open while the pointer is over either the pet or panel, then closes about 200ms after leaving both.
- Ran `to-spec` without another interview, using the existing offscreen `PetWindow` interaction seam plus deterministic provider fixtures. Published the full Chinese specification as `DLI1996/desktop-pet-stock#1` with `ready-for-agent`; enabling Issues and creating the missing canonical label were required on the origin fork.
- Updated issue #1 with the confirmed startup and loading contract: launch at macOS login, default each app session to the US Market view, align row names/values left/right, preload all summaries behind a list-wide wireframe, defer Detail series until activation, and use 350ms/200ms chart-tooltip intent timing.
- Ran `to-tickets`, confirmed granularity and blocking edges one question at a time, and published issues #2–#5 with `ready-for-agent`. The first implementation target is #2 for a runnable US/VIX demo; #5 is independently ready, while #3 and #4 are blocked only by #2.
- Implemented Issue #2 test-first: added deterministic VIX summary parsing, a US-default in-window market panel, lazy same-panel VIX detail, OHLC/source/date rendering, and 350ms/200ms tooltip/close intent.
- Verified the issue #2 focused interaction/parser tests and the full offscreen suite; no VIX loader runs during list rendering until the panel opens, and list rendering never constructs detail series.
- Fixed the Issue #2 review findings: explicitly hid the child panel during startup, applied the 200ms close intent in demo mode, and changed tooltip hit-testing to rendered-point radius checks with delayed dismissal.
- Applied Standards review cleanup by renaming `MarketPanel.screen` to `content_view`, annotating Qt event overrides, and removing the pure close delegation; focused regression tests pass.

### Files Created/Modified
- `.planning/2026-08-23-market-safety-overhaul/task_plan.md`
- `.planning/2026-08-23-market-safety-overhaul/findings.md`
- `.planning/2026-08-23-market-safety-overhaul/progress.md`
- `tests/test_quote_provider.py` (uncommitted red test from diagnosis)
- `src/quote_provider.py` (exchange-time normalization)
- `config.json`, `src/pet_window.py`, `tests/test_pet_window_safety.py`, and `README.md` (opt-in auto actions)
- `src/quote_provider.py` and `tests/test_quote_provider.py` (central quote validation)
- `requirements.in`, `requirements.txt`, `README.md`, `AGENTS.md`, and `build_app.sh` (reproducible lock workflow)
- `src/vix_view.py`, `src/pet_window.py`, `tests/test_vix_smoke.py`, and `tests/fixtures/vix_history.csv` (Phase 9 VIX smoke slice)
- `src/vix_provider.py` and `tests/test_vix_provider.py` (Phase 9 review fixes)

## Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Original suite before regression | 11 passing | 11 passing | pass |
| `TestMarketOpen.test_uses_exchange_timezone_for_aware_datetime` | Red before fix | Fails consistently at 02:00 UTC / 10:00 Shanghai | expected red |
| Minimized timezone regression after fix | 1 passing | 1 passing | pass |
| Quote-provider tests after fix | 7 passing | 7 passing | pass |
| Full suite after Iteration 1 | 12 passing | 12 passing | pass |
| Iteration 2 default-disabled repro before fix | No browser launch | Browser launch called once | expected red |
| Iteration 2 safety tests after fix | 2 passing | 2 passing | pass |
| Full suite after Iteration 2 | 14 passing | 14 passing | pass |
| Iteration 3 unsafe quote repro before fix | Reject malformed quote | `QuoteResult.ok=True` for all three cases | expected red |
| Quote-provider tests after Iteration 3 | 8 passing | 8 passing | pass |
| Full suite after Iteration 3 | 15 passing | 15 passing | pass |
| Iteration 4 lower-bound check before fix | No open-ended constraints | Three lower-bound lines found | expected red |
| Iteration 4 lock verification | Offline hash-checked install | 10 packages checked | pass |
| Full suite after Iteration 4 | 15 passing | 15 passing | pass |
| Final clean-tree verification | Lock check and full suite | 10 packages checked; 15 tests passing | pass |
| Phase 8 focused tests | Quote provider and config | 13 tests passing | pass |
| Phase 8 full verification | `compileall` and offscreen suite | Compilation passed; 20 tests passing | pass |
| Phase 9 VIX smoke before implementation | Hover exposes one `VIX` action | Zero visible menus after 400 ms | expected red |
| Phase 9 focused smoke after implementation | Menu, loading, ready data, and failure state | 1 passing | pass |
| Phase 9 full verification | Offscreen suite, compilation, diff check | 21 passing; compilation and diff check passed | pass |
| Phase 9 review-fix focused verification | Provider parsing and VIX smoke | 3 passing | pass |
| Phase 9 review-fix full verification | Offscreen suite, compilation, diff check | 23 passing; compilation and diff check passed | pass |
| Phase 11 original-hover regression before fix | Quote card visible; no menu | Card visible; one VIX menu visible | expected red |
| Phase 11 original-hover regression after fix | Quote card visible; no menu | 1 passing | pass |
| Phase 11 full verification after hover fix | Offscreen suite | 23 passing | pass |
| Phase 11 China quote repro | Default production provider returns a quote | `接口返回空数据` twice | expected red |
| Phase 11 explicit China quote connection | Opted-in provider returns `sh000001` | `3912.52`, `+0.59%`, Sina source | pass |

## Error Log
| Error | Resolution |
|-------|------------|
| `.venv/bin/python` missing | Used configured Codex venv for stdlib-only tests. |
| Plan replacement patch rejected | Split replacement into separate delete and add operations. |
| Plan commit blocked by trailing blank lines | Removed the whitespace and restaged the corrected files. |
| PySide6 import failed in the lightweight venv | Use the repository-local environment for the real UI behavior test. |
| `uv venv` default cache was sandbox-blocked | Redirect uv cache to a task-scoped writable directory. |
| uv managed-Python directory was sandbox-blocked | Redirect uv managed Python storage to a task-scoped writable directory. |
| Managed Python download failed DNS lookup | Request network access for the resolved uv environment command. |
| Combined product/planning patch context mismatch | Split the patch and applied each part against current content. |
| Quote-validation test failed after the privacy default changed | Marked its mocked direct provider as explicitly opted in; it now tests validation rather than fallback permission. |
| Detached worktree switch could not write Git's external worktree metadata | Re-ran the resolved `git switch --detach 41d7db5...` with approved access. |
| Focused VIX smoke command found no worktree-local `.venv` | Reused the main worktree's existing locked Python 3.12 environment with PySide6 6.11.2. |
| Offscreen `QTest.qWait()` prevented the Python loader thread from acquiring the GIL | Waited on the deterministic loader event, then processed queued Qt events. |
| China quote trial relaunch exited immediately | Found and stopped the prior confirmed app PID holding the single-instance lock, then relaunched successfully. |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 11 specification is published as GitHub issue #1. |
| Where am I going? | Implement issue #2 for the first demo, then work the remaining ready frontier while Phase 10 governance decisions remain separate. |
| What's the goal? | Add the China / US Market panel and VIX alert without changing the existing watched-instrument reaction model. |
| What have I learned? | See `findings.md`. |
| What have I done? | Created the plan and preserved the first red loop. |
