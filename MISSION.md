# Mission: Safely Extend desktop-pet-stock Markets

## Why
Understand the application well enough to change or add supported stock exchanges without silently showing incorrect symbols, prices, trading status, or triggering surprising desktop actions.

## Success looks like
- Trace a quote from configuration or menu selection through the provider into the UI and state machine.
- Identify every exchange-specific assumption before adding a market.
- Evaluate network, file, process-launching, data-quality, and asset-licensing risks.
- Design and test an exchange change before relying on it.

## Constraints
- Learn through this repository's real code and short, interactive lessons.
- Prefer primary documentation and observable tests over assumptions.

## Out of scope
- Investment advice, trading strategies, and order execution.
- A full PySide6 course unrelated to changing markets safely.
