# Findings & Decisions

## Requirements
- Fix exchange-time handling so market state uses the exchange timezone rather than the Mac's local timezone.
- Disable browser, application, and file-opening side effects unless the user explicitly opts in.
- Validate quote data before it reaches the state machine or triggers effects.
- Replace open-ended dependency resolution with a reproducible uv-compatible lock workflow.
- For each item: diagnose, implement test-first, commit, and run a two-axis code review.

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

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| GitHub CLI token is expired | Fork creation used the authenticated GitHub browser; Git pushes use SSH. |

## Resources
- `AGENTS.md`
- `docs/agents/domain.md`
- `src/quote_provider.py`
- `src/pet_window.py`
- `tests/test_quote_provider.py`
- `requirements.txt`
- `RESOURCES.md`
