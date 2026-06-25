# Contributing

## Before You Start

Read [DISCLAIMER.md](DISCLAIMER.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Contributions that enable targeting of private individuals or mass harassment will not be merged.

## Dev Setup

```bash
py -3.10 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Frontend:

```bash
cd frontend
npm install
```

## Running Tests

```bash
py -3.10 -m pytest
```

All PRs must pass the test suite. Add tests for new behavior.

## Code Style

- Python: follow existing patterns — type hints, SQLAlchemy 2.0 ORM style, Pydantic models
- No bare `python` or `pip` — use `py -3.10` (multiple Python versions on target dev machine)
- TypeScript: strict mode, no `any`, React Query for data fetching
- Tailwind only — no inline styles, no external CSS libraries

## Pull Requests

1. Fork the repo and branch from `main`
2. Make changes on a feature branch (`feat/...`, `fix/...`, `chore/...`)
3. Write or update tests covering the change
4. Run `py -3.10 -m pytest` and confirm passing
5. Open a PR with a clear description of what changed and why

## What We Accept

- Bug fixes with reproduction steps
- New OSINT signal extractors (new platform pivots, new link patterns)
- API endpoint additions
- Frontend improvements that follow the Warp design system
- Test coverage improvements
- Documentation fixes

## What We Won't Merge

- Features designed to bulk-scrape or mass-identify private users
- Anything that circumvents 4chan's API rate limits or Terms of Service
- Dependencies without clear justification
- Code that stores or transmits scraped data to third-party services

## Commit Format

```
type: short description

feat: add steam profile pivot
fix: handle missing trip field in post parser
chore: update dependencies
```

## Architecture Decisions

See [ARCHITECTURE.md](ARCHITECTURE.md) for data flow, module responsibilities, and design rationale before adding new modules.
