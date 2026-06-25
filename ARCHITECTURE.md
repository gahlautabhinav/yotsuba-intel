# Architecture

## Overview

Yotsuba Intel is a local-first OSINT workstation. All data stays on disk. The system has three entry points that share a common storage layer:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI (Click)   │    │  API (FastAPI)   │    │ React Dashboard │
│   chan scrape   │    │  :8003           │    │ :5174           │
│   chan profile  │    │                 │    │                 │
│   chan correlate│    │                 │    │                 │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                     │                       │
         └─────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  storage/repository  │
                    │  SQLAlchemy 2.0 ORM  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  SQLite (WAL mode)   │
                    │  chan_osint.db        │
                    └─────────────────────┘
```

## Module Responsibilities

### `scraper/`

- `api_client.py` — wraps `https://a.4cdn.org/{board}/thread/{no}.json`, parses thread URLs, handles 404/gone responses
- `post_parser.py` — normalizes raw JSON post objects into flat dicts, handles file metadata
- `link_extractor.py` — regex + heuristic extraction of social handles, emails, PGP fingerprints from post body HTML and text
- `image_downloader.py` — downloads attached files, extracts EXIF metadata, GPS coordinates, author tags
- `archive_client.py` — queries 4plebs/warosu JSON APIs for historical posts

### `storage/`

- `engine.py` — SQLite engine, WAL pragma, session factory, `init_db()`, `Base`
- `models.py` — SQLAlchemy ORM models: `Thread`, `Post`, `SocialLink`, `PivotResult`, `Email`, `PgpKey`, `Tripcode`, `FileDownload`, `Md5Correlation`, `ArchivePost`
- `repository.py` — all DB reads/writes go through `Repository`. No raw SQL outside this file.

### `analysis/`

- `temporal_profiler.py` — infers timezone from post timestamp histogram; outputs UTC offset guess + confidence + 24h activity histogram
- `tripcode_profiler.py` — aggregates tripcode stats across threads: boards, countries, name variants, social links, emails, PGP keys
- `md5_correlator.py` — scores file MD5 hashes for identity signal vs. meme/viral image; factors: post count, board spread, tripcode co-occurrence

### `pivot/`

- `resolver.py` — dispatches social links to platform-specific handlers
- `platforms/` — one file per platform: GitHub, Reddit, Twitter, Steam, Keybase, Pastebin, Telegram, Instagram, PGP keyserver, email (HIBP + Gravatar), generic URL

### `api/`

- `main.py` — FastAPI app, CORS, lifespan `init_db()`, router mounts
- `dependencies.py` — `get_repo()` dependency injection
- `routes/scrape.py` — POST `/scrape/` starts background thread, returns `job_id`; GET `/scrape/stream/{job_id}` SSE stream of log lines

### `cli/`

- `main.py` — Click group entry point (`chan`)
- `commands/` — one file per command: scrape, serve, profile, correlate, archive, pivot, show, export, watch

### `frontend/src/`

- `api/client.ts` — typed fetch wrapper, all API calls, `scrapeStreamUrl()` for SSE
- `pages/` — Dashboard, Threads, ThreadDetail, Tripcodes, TripDetail, Images, Correlate, Archive
- `components/` — StatCard, Badge, Skeleton, layout primitives

## Data Flow: Thread Scrape

```
User input (URL)
     │
     ▼
ChanAPIClient.parse_thread_url()  →  (board, thread_no)
     │
     ▼
ChanAPIClient.get_thread()  →  raw JSON from a.4cdn.org
     │
     ▼
parse_thread()  →  thread_data dict + list of post dicts
     │
     ├─▶ Repository.save_thread()
     │
     └─▶ for each post:
           Repository.save_post()
           extract_from_post()  →  links, emails, pgp_fingerprints
           Repository.save_social_link() / save_email() / save_pgp_key()
           Repository.upsert_tripcode() + update_tripcode_stats()
```

## SSE Scrape Streaming

```
POST /scrape/          →  ScrapeJob created, background thread started, job_id returned
GET  /scrape/stream/   →  SSE async generator polls job.logs every 150ms
                           sends data: <line>\n\n per log entry
                           sends event: done\ndata: complete\n\n on finish
Frontend EventSource   →  appends to terminal log div, auto-scrolls, closes on done event
```

## Database Schema (key tables)

```
threads (id, board, thread_no, subject, scraped_at, post_count, unique_ips, is_archived, raw_url)
  └── posts (id, thread_id, post_no, posted_at, name, trip, country, body_text, has_file, file_md5, file_ext)
        ├── social_links (id, post_id, platform, raw_url, handle, confidence)
        │     └── pivot_results (id, link_id, status, profile_data)
        ├── emails (id, post_id, email, source, breach_count, gravatar_url)
        ├── pgp_keys (id, post_id, fingerprint, key_id, real_name)
        └── file_downloads (id, post_id, file_md5, local_path, gps_lat, gps_lon, camera_make)

tripcodes (id, trip, trip_strength, post_count, boards_seen, timezone_guess, timezone_confidence)
archive_posts (id, source, board, thread_no, post_no, posted_at, name, trip, body_text, file_md5)
md5_correlations (id, file_md5, post_count, board_count, confidence, is_likely_meme)
```

## Design Decisions

**SQLite over PostgreSQL** — single-user local research tool; WAL mode handles concurrent reads from API + CLI without contention.

**Background thread for scraping** — 4chan threads can have thousands of posts; synchronous scraping would timeout HTTP clients. Background thread + SSE polling gives live feedback without blocking.

**Repository pattern** — all DB access through `Repository`. Keeps routes and CLI commands thin, makes testing with in-memory SQLite straightforward (`StaticPool` for shared connection in tests).

**No auth on API** — designed for localhost only. Exposing to a network requires adding auth middleware (see SECURITY.md).

**Confidence scoring** — MD5 and tripcode correlations produce float confidence values, not binary matches. Callers decide the threshold for actionable signal.
