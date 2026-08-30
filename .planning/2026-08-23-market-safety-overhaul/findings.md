# Findings & Decisions

## Requirements
- Fix exchange-time handling so market state uses the exchange timezone rather than the Mac's local timezone.
- Disable browser, application, and file-opening side effects unless the user explicitly opts in.
- Validate quote data before it reaches the state machine or triggers effects.
- Replace open-ended dependency resolution with a reproducible uv-compatible lock workflow.
- For each item: diagnose, implement test-first, commit, and run a two-axis code review.
- Phase 9 is now limited to a VIX desktop-interaction smoke slice: one hover menu item and one Cboe-history detail view, with no refresh, registry, persistence, dashboard, fallback, or chart dependency.

## Research Findings
- `is_market_open()` reads `datetime.time()` and `weekday()` without exchange-time conversion.
- A minimized test using `2026-08-20T02:00:00+00:00` fails: Shanghai local time is Thursday 10:00, but the function returns closed.
- A targeted probe confirmed the input remained at `02:00`; converting with `ZoneInfo("Asia/Shanghai")` produced Thursday `10:00`. A naive Thursday `10:00` already passes, falsifying the session-range and weekday hypotheses.
- `PetWindow._auto_action()` can open Douyin, launch WPS, or append to `~/Documents/牛来上班记录.txt` after quote-driven state transitions.
- `SkillBridgeProvider` and `SinaHttpProvider` normalize data structurally but apply no centralized finite/range/consistency policy.
- `requirements.txt` uses lower bounds only: `PySide6>=6.6`, `Pillow>=10.0`, and `requests>=2.28`.
- Direct provider use exposes watched symbols and the user's IP; the Sina endpoint lacks a recorded authoritative API contract.
- Bundled character media has explicit redistribution/commercial-use licensing uncertainty.
- Iteration 1 review reported zero Standards findings and zero Spec findings.
- Iteration 2 has no pure policy seam: quote-driven effects call `_auto_action()` inside the PySide `PetWindow` class. A config-only test would not exercise the real side-effect path.
- The lightweight Codex venv does not contain PySide6, so an offscreen UI test requires the repository's documented `.venv`.
- The offscreen repro showed missing, false, and true configs each launched the browser once. `_auto_action()` ignored configuration entirely; no caller-side opt-in exists.
- A minimized `StockDataProvider` test showed `NaN`, zero, and inconsistent quote values were all marked successful and could reach the state machine.
- The previous dependency file held only three lower bounds; compiling a hash-locked `requirements.txt` from a new `requirements.in` resolved ten exact packages and passed an offline hash-checked install.
- `load_config()` passed malformed JSON through as a startup exception; a default-plus-per-key validation boundary can preserve valid opt-ins while rejecting malformed fields.
- Phase 8's minimized synchronous test reproducibly shows `StockDataProvider.get_quote()` calls Sina once without consent. The fallback is unconditional when bridge data is absent, the constructor has no policy input, and `PetWindow` is the only production constructor call.
- `StockDataProvider(enable_http_fallback=False)` is a compact shared policy seam: it blocks the direct adapter for both synchronous and asynchronous requests, while `PetWindow` passes the validated user setting through unchanged.
- `PetWindow` already owns a single-shot 350 ms hover timer and uses `QMenu` and `QPainter`; these are the narrow existing seams for the VIX slice.
- The repository already uses `urllib.request`, so the Cboe CSV fetch needs no new HTTP or chart dependency.
- The first offscreen VIX smoke run failed after 400 ms with zero visible menus, proving the missing hover interaction before implementation.
- `QTest.qWait()` holds the Python GIL in this offscreen setup; deterministic async checks wait on the loader event, then process queued Qt events.
- Phase 11 clarification: the China / US choice filters the watched-instrument catalog under “更换关注标的”; it is not an active data mode, and VIX is outside this decision.
- Phase 11 menu decision: use native nested catalogs, `更换关注标的 → 中国 / 美国 → watched instrument`; there is no persistent market-switch state.
- Phase 11 US catalog scope: the first version contains only VIX; no US indices, stocks, ETFs, or custom tickers.
- Phase 11 quick-spike override: remove VIX from the automatic hover path first so hover returns to the original quote-card-only interaction; defer the remaining catalog questions while testing the original China quote connection. The user's `zn` referred informally to that existing China market behavior, not a ticker.
- The VIX provider and detail view remain available for a later explicit menu action, but `PetWindow` no longer imports or opens them automatically.
- The live “行情走丢了” result was deterministic: `quote.json` was absent and the safe default `enable_http_fallback=false` left the provider with no source. A one-session explicit opt-in returned `sh000001` successfully from Sina and drove the existing card/state path.
- Live smoke found a separate unresolved interaction bug: after choosing `爆拉！`, choosing another index does not switch back from the forced surge/demo presentation. This is recorded as an observed symptom only; root cause has not yet been diagnosed.
- Phase 11 visual direction changed after reviewing the supplied macOS reference: the compact custom hover panel and separate detail window may replace the original mini quote card/native hover-menu presentation. The reference's Level 2 label, extra US metrics, intraday periods, settings, pinning, and add-metric affordance are not implicitly in scope.
- Phase 11 market-panel decision: use explicit `中国 / 美国` switch buttons; show one market view at a time instead of mixing both markets in one list.
- Phase 11 frontend refinement: the active row needs a persistent visual highlight; reserve a `＋ 添加指标` footer for later implementation.
- The detail design must expose latest value/change, high, low, open, previous close, data source, and point inspection for exact time/value. Backend provider selection is deliberately deferred until this frontend contract is confirmed.
- Phase 11 navigation decision: detail replaces the list inside the same market panel and `返回` restores the list; no separate OS detail window.
- The market panel is presentation/navigation only. Selecting a China row must continue through the existing watched-instrument and `FLAT / RISE / SURGE / FALL` reaction path, including its current animation/effect behavior. Opening VIX detail must not drive that reaction path.
- Future US equity indices such as S&P 500 and Nasdaq are watched instruments, not metrics: selecting one replaces the current China watched instrument and drives the existing market reaction. VIX remains a metric and never drives the pet animation.
- A user-approved Perplexity standard search (not Deep Research) recommended a minimal VIX rule: enter PANIC on the latest completed daily close at `VIX >= 30`; recover only after `VIX < 25` for two consecutive trading-day closes; do not change state intraday. It recommended fixed levels over a 52-week moving average for v1, with a trailing one-year percentile as a possible later adaptive guardrail.
- The `30 / 25` thresholds are an editorial product recommendation, not an official universal boundary. Cboe/FRED support the VIX definition and daily-close data contract, but threshold suitability still needs an independent historical frequency replay before adoption.
- A second user-requested Perplexity ordinary Search clarified the semantics: VIX is an options-derived estimate of the expected magnitude of S&P 500 movement over roughly 30 days. It is direction-neutral, mostly reflects SPX option pricing/expectations, and does not itself mean the market is falling or predict a crash.
- That search recommended keeping watched-index direction authoritative and using VIX as a graded high-volatility/uncertainty overlay. For China instruments VIX is global/US volatility context, not a direct China-risk measure. The adopted design limits this to a visual alert overlay and adds no PANIC animation state.
- Phase 11 product decision simplified this further: VIX does not alter, intensify, replace, or temporarily override any pet animation. It only controls one independent high-volatility alert overlay while the watched instrument remains the sole driver of `FLAT / RISE / SURGE / FALL`.
- The VIX alert is a small persistent badge beside the pet, including while the market panel is closed; clicking the badge opens VIX detail directly.
- The Market panel remains open while the pointer is over either the pet or panel. Leaving both starts an approximately 200ms close delay; the next hover restores the list level while preserving the last Market view and Active row.
- The complete Phase 11 Chinese specification is published as origin issue #1 with `ready-for-agent`. The origin fork had Issues disabled and lacked the canonical label, so Issues were enabled and only the required label was created before publishing.
- Issue #1 now requires the packaged app to launch at macOS login while preserving the single-instance boundary. Each new app session initializes the US Market view, but browsing a view still does not change the configured Watched instrument.
- Market list rows use a left-aligned name and right-aligned current value. The current view's summaries preload as one list state behind wireframe rows; row detail/history loaders are not activated during list loading.
- Historical Detail series load only after row activation. Chart point inspection uses a 350ms intent delay and an approximately 200ms dismissal delay, with no additional request on tooltip movement.
- The approved tracer-bullet breakdown is published as ready-for-agent issues #2–#5 under parent spec #1. Issue #2 (US/VIX runnable demo) and issue #5 (macOS login launch) are the initial frontier; #3 (China Market view) and #4 (VIX alert) each depend only on #2.
- The ask-perplexity workflow text previously defaulted decision questions to Deep Research. A Luna medium subagent changed the local skill to default to ordinary Search and require an explicit user/command request for Deep Research; no product-repository files were touched.
- The current provider is China-only (`sh`/`sz`/`bj` six-digit symbols, Shanghai hours, Sina/bridge data), so selecting a US watched instrument will require a separate provider contract in implementation.
- Phase 9 review found Cboe access/parsing mixed into the QWidget module, missing parser edge-case coverage, and unrelated local tooling visible as untracked changes.
- Re-review clarified that repository-wide ignore policy is outside the VIX slice; worktree-local Git exclusion preserves the files without a tracked `.gitignore` change.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Normalize aware datetimes to an explicit exchange zone | Makes the contract deterministic across host timezones. |
| Introduce a testable safety-policy seam before changing UI behavior | PySide is absent in the lightweight test environment; policy should be pure and independently testable. |
| Centralize validation at the canonical quote boundary | Both bridge and HTTP providers must obey the same safety rules. |
| Diagnose lock format before choosing one | The repository has requirements files but no `pyproject.toml`; the solution must fit its uv workflow. |
| Gate `_auto_action()` itself with `enable_auto_actions`, default false | This last shared boundary protects every browser/app/file side effect from every caller. |
| Validate normalized quote fields in `StockDataProvider.get_quote()` | It is the one shared boundary after either provider and before every state-machine/UI consumer. |
| Keep direct requirements in `requirements.in`; commit generated `requirements.txt` | Preserves intentional version policy while making normal installation reproducible and hash-checked. |
| Gate Sina fallback in `StockDataProvider` and pass the config opt-in from `PetWindow` | This shared boundary covers synchronous and asynchronous fetching without changing the HTTP adapter. |
| Replace the prior Phase 9 calendar task with the delegated VIX smoke slice | The current task explicitly narrows Phase 9 to this UI behavior and defers the calendar work. |
| Keep only the most recent 60 valid daily closes | This bounds painting work and matches the requested recent-history view without persistence or refresh machinery. |
| Do not fold a China/US market switch into Phase 9 | The proposed follow-up was withdrawn before completion; retain the existing index preset behavior. |
| Keep Cboe fetching/parsing in `vix_provider.py` | Preserves the repository's existing UI/data separation with one small provider module. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| GitHub CLI token is expired | Fork creation used the authenticated GitHub browser; Git pushes use SSH. |

## Residual Risks
- Direct provider requests still disclose the selected symbol and client IP; resolving that needs a provider or proxy decision.
- Sina's endpoint remains an undocumented public interface; provider-contract assurance needs an authoritative source or agreement.
- Market hours exclude China-specific holidays and ad-hoc closures; adding a maintained trading-calendar source is a separate product decision.
- Character artwork and audio still require a licensing decision before redistribution or commercial use.

## Resources
- `AGENTS.md`
- `docs/agents/domain.md`
- `src/quote_provider.py`
- `src/pet_window.py`
- `tests/test_quote_provider.py`
- `requirements.txt`
- `RESOURCES.md`
