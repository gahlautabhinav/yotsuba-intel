# Yotsuba Intel

4chan thread OSINT tool — scrape, analyze, and pivot on signals extracted from 4chan threads.

## Features

- **Thread scraping** — pulls posts via 4chan public JSON API, stores in SQLite
- **Tripcode profiling** — tracks tripcodes across boards, infers timezone from post timestamps
- **MD5 correlator** — finds same image posted across threads/boards, scores identity confidence
- **Social link extraction** — detects GitHub, Twitter/X, Reddit, Telegram, Steam, Keybase handles in post bodies
- **Email pivoting** — extracts emails, checks HIBP breaches, Gravatar lookups
- **PGP key extraction** — finds fingerprints, looks up keyservers
- **EXIF analysis** — extracts GPS, camera make/model, author tags from downloaded images
- **Archive search** — queries 4chan archive sites (4plebs, warosu, etc.) by tripcode, MD5, or name
- **Live scrape streaming** — SSE terminal-style output while scraping
- **REST API** — FastAPI backend on port 8003
- **React dashboard** — Warp-themed UI on port 5174

## Stack

| Layer | Technology |
|-------|-----------|
| CLI | Python 3.10 + Click + Rich |
| API | FastAPI + uvicorn |
| Storage | SQLite (WAL mode) + SQLAlchemy 2.0 ORM |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Data fetching | React Query + Zustand |
| Charts | Recharts |
| Maps | Leaflet |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
# Create venv
py -3.10 -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/macOS

# Install
pip install -e ".[dev]"

# Start API server (port 8003)
chan serve
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # opens http://localhost:5174
```

### CLI Usage

```bash
# Scrape a thread
chan scrape https://boards.4chan.org/g/thread/12345678

# Profile a tripcode
chan profile !abc123XYZ

# Correlate an MD5 hash
chan correlate md5 <base64-md5>

# Search archives
chan archive search --trip !abc123XYZ --board g

# Export data
chan export threads
chan export tripcodes
```

## Project Structure

```
chan-osint/
├── api/              # FastAPI app + routes
│   └── routes/       # threads, posts, links, emails, tripcodes, archive, correlate, scrape
├── analysis/         # MD5 correlator, temporal profiler, tripcode profiler
├── cli/              # Click CLI commands
├── config/           # Pydantic settings
├── pivot/            # Social platform pivot handlers
│   └── platforms/    # GitHub, Reddit, Twitter, Steam, Keybase, PGP, etc.
├── scraper/          # 4chan API client, post parser, link extractor, image downloader
├── storage/          # SQLAlchemy models, engine, repository
├── tests/            # pytest test suite
└── frontend/         # React dashboard
    └── src/
        ├── api/      # typed API client
        ├── components/
        └── pages/    # Dashboard, Threads, ThreadDetail, Tripcodes, Images, Correlate, Archive
```

## Running Tests

```bash
py -3.10 -m pytest
```

## Configuration

Copy `.env.example` to `.env` and set:

```env
DATABASE_URL=sqlite:///./chan_osint.db
```

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

See [DISCLAIMER.md](DISCLAIMER.md) for legal and ethical use guidelines.
