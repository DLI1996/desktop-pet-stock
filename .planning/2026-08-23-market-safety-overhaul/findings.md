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
- `PetWindow._auto_action()` can open Douyin, launch WPS, or append to `~/Documents/牛来上班记录.txt` after quote-driven state transitions.
- `SkillBridgeProvider` and `SinaHttpProvider` normalize data structurally but apply no centralized finite/range/consistency policy.
- `requirements.txt` uses lower bounds only: `PySide6>=6.6`, `Pillow>=10.0`, and `requests>=2.28`.
- Direct provider use exposes watched symbols and the user's IP; the Sina endpoint lacks a recorded authoritative API contract.
- Bundled character media has explicit redistribution/commercial-use licensing uncertainty.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Normalize aware datetimes to an explicit exchange zone | Makes the contract deterministic across host timezones. |
| Introduce a testable safety-policy seam before changing UI behavior | PySide is absent in the lightweight test environment; policy should be pure and independently testable. |
| Centralize validation at the canonical quote boundary | Both bridge and HTTP providers must obey the same safety rules. |
| Diagnose lock format before choosing one | The repository has requirements files but no `pyproject.toml`; the solution must fit its uv workflow. |

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
