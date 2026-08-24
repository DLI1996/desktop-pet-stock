# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists: it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Domain-modeling workflows create them lazily when terms or decisions are resolved.

## File structure

This is a single-context repo:

```text
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

## Use the glossary's vocabulary

When output names a domain concept—in an issue title, refactor proposal, hypothesis, or test—use the term defined in `CONTEXT.md`. Avoid synonyms the glossary explicitly rejects.

If the needed concept is absent, reconsider whether the project uses that language or note a genuine gap for `/domain-modeling`.

## Flag ADR conflicts

Surface contradictions with existing ADRs explicitly instead of silently overriding them:

> _Contradicts ADR-0007, but worth reopening because…_
