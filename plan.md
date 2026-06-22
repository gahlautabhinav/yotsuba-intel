# Plan: Yotsuba Intel — 4chan Thread OSINT Tool

## Context

Standalone OSINT tool to scrape 4chan threads via public JSON API, store all post data in SQLite, extract social media links/handles/emails/PGP from post text, correlate identities across threads and boards via archives, download images and extract EXIF metadata, resolve all social links into profile snapshots, and expose everything through both a CLI and a web dashboard UI.

IP addresses NOT available via 4chan's public API. Available identity signals: country codes (geo-flag boards), per-thread hashed poster IDs, tripcodes, non-anonymous name fields, original filenames, file MD5 hashes, emails/PGP fingerprints in post text, and social links dropped in posts.

---

## Repository

**GitHub:** https://github.com/gahlautabhinav/yotsuba-intel
**Default branch:** `main`
**Branch strategy:** Each phase = dedicated feature branch → PR → merge to main. Never commit directly to main.

Branch naming: `feat/phase-N-<short-name>`
Example: `feat/phase-1-core-infra`, `feat/phase-4-pivot-engine`

---

## Project Location

`d:\random_tools\chan-osint\`
Sibling to `twitter-osint`. Standalone — no shared code.

---

## Architecture: Modular Monolith + Web UI

```
chan-osint/
├── scraper/
│   ├── __init__.py
│   ├── api_client.py          # 4chan JSON API + rate limiter (1 req/sec)
│   ├── archive_client.py      # 4plebs/desuarchive/warosu API clients
│   ├── post_parser.py         # Raw JSON → PostData TypedDicts
│   ├── link_extractor.py      # Regex: social URLs, emails, PGP fingerprints
│   └── image_downloader.py    # Download images, run exiftool, store EXIF
├── pivot/
│   ├── __init__.py
│   ├── resolver.py            # Orchestrates pivot jobs per extracted link/email
│   └── platforms/
│       ├── __init__.py
│       ├── base.py            # AbstractPlatformFetcher interface
│       ├── twitter.py         # twitter.com / x.com profile fetch (og: meta)
│       ├── github.py          # github.com API: name, email, commit emails, location
│       ├── telegram.py        # t.me profile fetch
│       ├── instagram.py       # instagram.com (best-effort, blocks heavily)
│       ├── reddit.py          # reddit.com profile: name, linked accounts, location
│       ├── keybase.py         # keybase.io: PGP → verified Twitter/GitHub/domain
│       ├── pastebin.py        # pastebin.com: fetch content, extract paths/usernames
│       ├── steam.py           # steamcommunity.com/id/handle → real name, location
│       ├── email_pivot.py     # Email → HaveIBeenPwned breach check + gravatar
│       ├── pgp_keyserver.py   # PGP fingerprint → keyserver lookup → real name + email
│       └── generic.py         # Fallback: HEAD + title + og:tags for unknown URLs
├── analysis/
│   ├── __init__.py
│   ├── tripcode_profiler.py   # Aggregate all posts by trip across threads/boards
│   ├── md5_correlator.py      # Cross-thread/board file MD5 correlation via archives
│   ├── temporal_profiler.py   # Time-of-day heatmap → timezone inference
│   └── stylometry.py          # Basic writing pattern analysis per identity cluster
├── storage/
│   ├── __init__.py
│   ├── engine.py              # SQLite engine factory, WAL mode
│   ├── models.py              # SQLAlchemy ORM models
│   └── repository.py          # Repository pattern — all DB access here
├── api/                       # ← Phase 8: FastAPI backend for web UI
│   ├── __init__.py
│   ├── main.py                # FastAPI app, CORS, lifespan
│   ├── dependencies.py        # DB session injection
│   └── routes/
│       ├── __init__.py
│       ├── threads.py         # GET /threads, GET /threads/{id}/posts
│       ├── posts.py           # GET /posts/{id}, GET /posts/{id}/links
│       ├── links.py           # GET /links, GET /links/{id}/pivot
│       ├── emails.py          # GET /emails
│       ├── tripcodes.py       # GET /tripcodes, GET /tripcodes/{trip}/profile
│       ├── archive.py         # POST /archive/search
│       ├── correlate.py       # POST /correlate/md5
│       └── scrape.py          # POST /scrape (trigger scrape job)
├── frontend/                  # ← Phase 9: React web dashboard
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── layout/        # Sidebar, topbar, shell
│   │   │   ├── threads/       # ThreadList, ThreadCard, PostFeed
│   │   │   ├── identity/      # TripcodeProfile, IdentityCard, SignalBadge
│   │   │   ├── pivot/         # PivotResults, PlatformIcon, ConfidenceBar
│   │   │   ├── map/           # EXIF GPS map (Leaflet)
│   │   │   ├── timeline/      # ActivityHeatmap, PostTimeline
│   │   │   └── common/        # Table, Badge, Spinner, Toast
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx  # Stats overview
│   │   │   ├── Threads.tsx    # Thread list + scrape form
│   │   │   ├── Thread.tsx     # Single thread drill-down
│   │   │   ├── Tripcodes.tsx  # All tripcodes table
│   │   │   ├── Profile.tsx    # Full identity profile for one trip
│   │   │   ├── Correlate.tsx  # MD5 cross-thread correlation view
│   │   │   ├── Archive.tsx    # Archive search UI
│   │   │   └── Images.tsx     # Image gallery + EXIF viewer + GPS map
│   │   ├── api/               # Typed API client (fetch wrappers)
│   │   └── store/             # Zustand or React Query state
│   └── public/
├── cli/
│   ├── __init__.py
│   ├── main.py                # Click group entry point
│   └── commands/
│       ├── __init__.py
│       ├── scrape.py          # `chan scrape <url>`
│       ├── watch.py           # `chan watch <url>` — live poll until 404
│       ├── pivot.py           # `chan pivot [--thread N] [--platform X]`
│       ├── archive.py         # `chan archive --trip X | --md5 X | --name X`
│       ├── profile.py         # `chan profile --trip X` — full identity aggregate
│       ├── correlate.py       # `chan correlate --md5 X` — cross-thread file link
│       ├── show.py            # `chan show threads|posts|links|emails|tripcodes`
│       ├── export.py          # `chan export <thread_id> --format csv|json`
│       └── serve.py           # `chan serve` — launch FastAPI + frontend dev server
├── config/
│   ├── __init__.py
│   └── settings.py            # Pydantic Settings, reads .env
├── tests/
│   ├── __init__.py
│   ├── test_post_parser.py
│   ├── test_link_extractor.py
│   ├── test_archive_client.py
│   └── fixtures/
│       └── sample_thread.json
├── .env.example
├── requirements.txt
├── pyproject.toml             # Entry point: `chan` CLI command
└── CLAUDE.md
```

---

## SQLite Schema (models.py)

### `threads`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| board | TEXT | e.g. "pol", "g", "biz" |
| thread_no | INTEGER | 4chan thread number |
| subject | TEXT | OP subject line |
| scraped_at | DATETIME | |
| post_count | INTEGER | |
| unique_ips | INTEGER | from OP field, if present |
| is_archived | BOOLEAN | |
| raw_url | TEXT | original URL provided |
UNIQUE: `(board, thread_no)`

### `posts`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| thread_id | INTEGER FK → threads.id | |
| post_no | INTEGER | 4chan post number |
| resto | INTEGER | 0=OP, else parent thread_no |
| posted_at | DATETIME | from UNIX timestamp |
| name | TEXT | poster name (default "Anonymous") |
| trip | TEXT | tripcode if present |
| poster_id | TEXT | 8-char per-thread hash (if board has IDs) |
| capcode | TEXT | mod/admin/dev if present |
| country | TEXT | ISO 2-letter code if geo-enabled board |
| country_name | TEXT | |
| body_html | TEXT | raw HTML comment |
| body_text | TEXT | stripped plain text |
| has_file | BOOLEAN | |
| filename | TEXT | original filename (pre-rename) — can reveal device/user patterns |
| file_md5 | TEXT | base64 md5 — key cross-thread correlation signal |
| file_ext | TEXT | .jpg/.png/etc |
| file_size | INTEGER | bytes |
| img_w | INTEGER | |
| img_h | INTEGER | |
UNIQUE: `(thread_id, post_no)`

### `social_links`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| post_id | INTEGER FK → posts.id | |
| platform | TEXT | "twitter","github","telegram","instagram","reddit","youtube","discord","keybase","pastebin","steam","unknown" |
| raw_url | TEXT | as found in post |
| handle | TEXT | extracted username/handle if parseable |
| confidence | REAL | 0.0–1.0 |
| extracted_at | DATETIME | |
UNIQUE: `(post_id, raw_url)`

### `pivot_results`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| link_id | INTEGER FK → social_links.id | |
| status | TEXT | "pending","success","failed","blocked" |
| fetched_at | DATETIME | |
| http_status | INTEGER | response code |
| profile_data | TEXT | JSON blob: bio, follower_count, links_found, display_name, real_name, email, location, etc. |
| raw_html_snippet | TEXT | first 5000 chars of response for offline analysis |
| error | TEXT | |

### `emails`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| post_id | INTEGER FK → posts.id | |
| email | TEXT | extracted email address |
| source | TEXT | "name_field" / "body" |
| pivoted_at | DATETIME | nullable until pivoted |
| breach_count | INTEGER | from HIBP API |
| breach_names | TEXT | JSON list of breach names |
| gravatar_url | TEXT | if gravatar exists for this email |
| real_name_hint | TEXT | display name from gravatar or HIBP |
UNIQUE: `(post_id, email)`

### `pgp_keys`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| post_id | INTEGER FK → posts.id | |
| fingerprint | TEXT | 40-char hex fingerprint |
| key_id | TEXT | short 8/16 char key ID |
| real_name | TEXT | from keyserver UID |
| email | TEXT | from keyserver UID |
| keyserver_url | TEXT | where it was found |
| fetched_at | DATETIME | |
UNIQUE: `(post_id, fingerprint)`

### `tripcodes`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| trip | TEXT | the tripcode hash e.g. "!ABC123XYZ" |
| first_seen_at | DATETIME | |
| last_seen_at | DATETIME | |
| post_count | INTEGER | total posts with this trip |
| boards_seen | TEXT | JSON list of boards |
| handles_found | TEXT | JSON list of social handles from their posts |
| emails_found | TEXT | JSON list of emails from their posts |
| timezone_guess | TEXT | e.g. "UTC-5" from temporal analysis |
| countries_seen | TEXT | JSON list of countries (geo-boards) |
| notes | TEXT | manual analyst notes |
UNIQUE: `trip`

### `file_downloads`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| post_id | INTEGER FK → posts.id | |
| file_md5 | TEXT | base64 md5 (join key) |
| local_path | TEXT | where stored on disk |
| downloaded_at | DATETIME | |
| exif_json | TEXT | full exiftool JSON output |
| gps_lat | REAL | if EXIF GPS present |
| gps_lon | REAL | if EXIF GPS present |
| gps_location | TEXT | reverse-geocoded address |
| camera_make | TEXT | |
| camera_model | TEXT | |
| software | TEXT | editing software (Photoshop, GIMP, etc.) |
| author_tag | TEXT | EXIF Author/Artist/Creator field |
| create_date | DATETIME | from EXIF, not upload date |
UNIQUE: `(post_id, file_md5)`

### `archive_posts`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto |
| source | TEXT | "4plebs", "desuarchive", "warosu" |
| board | TEXT | |
| thread_no | INTEGER | |
| post_no | INTEGER | |
| posted_at | DATETIME | |
| name | TEXT | |
| trip | TEXT | |
| poster_id | TEXT | |
| country | TEXT | |
| body_text | TEXT | |
| file_md5 | TEXT | |
| filename | TEXT | |
| archive_url | TEXT | canonical URL on archive site |
| fetched_at | DATETIME | |
UNIQUE: `(source, board, post_no)`

---

## Key Component Details

### `scraper/api_client.py`
- `ChanAPIClient` class
- Token bucket rate limiter: max 1 req/sec
- `get_thread(board, thread_no) → dict` — fetches `https://a.4cdn.org/{board}/thread/{thread_no}.json`
- `parse_thread_url(url) → (board, thread_no)` — regex parses `4chan.org/{board}/thread/{no}`
- Uses `If-Modified-Since` header on repeat fetches
- Returns `None` on 404 (thread deleted)

### `scraper/archive_client.py`
Wrapper for multiple archive site APIs. All return `list[ArchivePost]`.

**4plebs API** (boards: pol, adv, f, hr, o, s4s, sp, tg, trv, tv, x):
```
GET https://archive.4plebs.org/_/api/chan/search/
  ?trip=!HASH          → all posts by tripcode
  ?md5=BASE64          → all posts containing that image
  ?name=John           → all posts with that name
  ?boards=pol,tv       → filter by board
```

**Desuarchive API** (boards: a, c, w, m, cgl, cm, f, n, jp, vp, etc.):
```
GET https://desuarchive.org/_/api/chan/search/?trip=!HASH
```

**Warosu API** (boards: g, sci, fa, ic, etc.):
```
GET https://warosu.org/api/v1/search?trip=!HASH&board=g
```

Rate limit: 1 req/2sec per archive site.

### `scraper/post_parser.py`
- `parse_thread(raw_json) → ThreadData, list[PostData]`
- TypedDicts: `ThreadData`, `PostData`, `FileData`
- Strips HTML from `com` field via `html.parser` to produce `body_text`
- Normalizes all timestamps to Python `datetime` objects
- Flags non-Anonymous names for priority processing

### `scraper/link_extractor.py`
- `extract_links(body_html, body_text, name_field) → ExtractedData`
- Returns `ExtractedData(links, emails, pgp_fingerprints)`

**Social link regexes:**
- Twitter/X: `(twitter\.com|x\.com)/(?:@?)([\w]+)` → 0.95
- GitHub: `github\.com/([\w\-]+)(?:/[\w\-]+)?` → 0.95
- Telegram: `t\.me/([\w]+)` → 0.95
- Instagram: `instagram\.com/([\w\.]+)` → 0.90
- Reddit: `reddit\.com/[ur]/([\w]+)` → 0.90
- YouTube: `youtube\.com/(?:@|c/|user/)([\w\-]+)` → 0.90
- Discord: `discord\.gg/([\w]+)` → 0.85
- Keybase: `keybase\.io/([\w]+)` → 0.95
- Pastebin: `pastebin\.com/([a-zA-Z0-9]+)` → 0.90
- Steam: `steamcommunity\.com/id/([\w]+)` → 0.90
- Generic URL: any `https?://` not matched above → 0.50

**Email regex** (body text AND name field):
```python
EMAIL_RE = r'[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}'
```

**PGP fingerprint regex:**
```python
PGP_FP_RE = r'(?:[0-9A-F]{4}\s?){10}'   # spaced format
PGP_FP_COMPACT = r'[0-9A-F]{40}'          # compact
```

### `scraper/image_downloader.py`
- Downloads from `https://i.4cdn.org/{board}/{tim}{ext}`
- Stores in `data/images/{board}/{file_md5}{ext}`
- Runs `exiftool -json {path}` → parses output
- Extracts: GPS coords, camera make/model, software, author/artist/creator, CreateDate
- Reverse geocodes GPS via `nominatim.openstreetmap.org` (free, no key)
- Skips download if file_md5 already in `file_downloads`
- Requires `exiftool` on PATH — warns if missing

### `pivot/platforms/github.py` — ENHANCED
Uses GitHub REST API (no auth = 60 req/hr; with token = 5000 req/hr):
```
GET https://api.github.com/users/{handle}
→ name (real name), email, company, location, blog, twitter_username, bio

GET https://api.github.com/users/{handle}/events
→ PushEvents → commits → author.name + author.email (real email even if hidden)
```

### `pivot/platforms/reddit.py`
```
GET https://www.reddit.com/user/{handle}/about.json
→ name, link_karma, comment_karma, created_utc
```

### `pivot/platforms/keybase.py`
```
GET https://keybase.io/{handle}/_/api/1.0/user/lookup.json?username={handle}
→ proofs: twitter, github, reddit, hackernews, domain
```
Cryptographically verified cross-platform links — highest confidence chain.

### `pivot/platforms/steam.py`
```
GET https://steamcommunity.com/id/{handle}/?xml=1
→ steamID64, realname (if set), location (if set), avatar, member since
```

### `pivot/platforms/pastebin.py`
```
GET https://pastebin.com/raw/{key}
→ raw text → extract: file paths (C:\Users\john\), hostnames, emails, handles
```

### `pivot/platforms/email_pivot.py`
- HIBP: `GET https://haveibeenpwned.com/api/v3/breachedaccount/{email}` (needs $3.50/mo key)
- Gravatar: `GET https://www.gravatar.com/{md5(email)}.json` → display name, linked accounts

### `pivot/platforms/pgp_keyserver.py`
```
GET https://keys.openpgp.org/vks/v1/by-fingerprint/{FINGERPRINT}
→ UID: "Real Name <email@domain.com>"
```

### `analysis/tripcode_profiler.py`
- `profile_trip(trip) → TripcodeProfile`
- Aggregates: local posts + archive_posts, timeline, boards, countries, social links, emails
- Calls `temporal_profiler.py` for timezone inference

### `analysis/md5_correlator.py`
- `correlate_md5(file_md5) → list[PostRef]`
- Queries local DB + archive APIs
- Returns all threads/boards/posters that used the same image

### `analysis/temporal_profiler.py`
- `infer_timezone(post_datetimes) → str`
- Hourly histogram → peak hours → timezone estimate with confidence score

### `api/main.py` — FastAPI backend (Phase 8)
- Serves all data from SQLite as JSON REST endpoints
- CORS enabled for local frontend dev (`localhost:5173`)
- Background task queue for scrape/pivot jobs triggered from UI
- `chan serve` command starts both API (`uvicorn`, port 8000) and frontend dev server

### Frontend (Phase 9) — React + Vite + Tailwind

**Design process:** Before implementing, user provides design md files. Use `/frontend-design:frontend-design` and `/ui-ux-pro-max:ui-ux-pro-max` skills to establish aesthetic direction, component design, and visual language before writing any UI code.

**Pages:**
| Page | Purpose |
|---|---|
| Dashboard | Stats cards: thread count, post count, tripcodes, emails found, pivot success rate |
| Threads | List all scraped threads, scrape form at top, click → Thread detail |
| Thread | Post feed with inline social links, emails, images; filter by poster/trip |
| Tripcodes | All tripcodes table: post count, boards, first/last seen, timezone guess |
| Profile | Full identity aggregate for one tripcode: timeline, heatmap, all signals found |
| Correlate | Input MD5 → see all posts/threads/users that image appeared in |
| Archive | Search form → results from 4plebs/desuarchive/warosu |
| Images | Gallery of downloaded images + EXIF panel + Leaflet GPS map for geotagged ones |

**Tech stack:**
- React 18 + TypeScript
- Vite (build)
- Tailwind CSS (styling)
- React Query (API state)
- Zustand (local UI state)
- Recharts (activity heatmap, timeline charts)
- Leaflet + react-leaflet (GPS map)
- Lucide React (icons)

---

## CLI Commands

```
# Scrape a thread
chan scrape https://boards.4chan.org/pol/thread/123456789
chan scrape https://boards.4chan.org/g/thread/987654321 --download-images

# Watch a live thread (poll until 404)
chan watch https://boards.4chan.org/pol/thread/123456789 --interval 30

# Pivot
chan pivot
chan pivot --thread 1
chan pivot --platform twitter,github,steam
chan pivot --platform email

# Archive search
chan archive --trip "!ABC123XYZ"
chan archive --md5 "BASE64=="
chan archive --name "John Smith"
chan archive --trip "!ABC123XYZ" --source 4plebs,desuarchive

# Identity
chan profile --trip "!ABC123XYZ"
chan correlate --md5 "BASE64=="

# Show
chan show threads
chan show posts 1
chan show links 1
chan show emails 1
chan show tripcodes
chan show pivots 1

# Export
chan export 1 --format csv
chan export 1 --format json
chan export --trip "!ABC123XYZ" --format json

# Web UI
chan serve                        # starts FastAPI on :8000 + frontend on :5173
chan serve --port 9000            # custom API port
```

---

## Data Flow

```
User provides URL
      ↓
cli/commands/scrape.py  OR  POST /api/scrape
      ↓
scraper/api_client.py  →  4chan JSON API (1 req/sec)
      ↓
scraper/post_parser.py  →  ThreadData + list[PostData]
      ↓
scraper/link_extractor.py  →  ExtractedData(links, emails, pgp_fingerprints)
      ↓
storage/repository.py  →  SQLite (threads, posts, social_links, emails, pgp_keys)
      ↓
[if --download-images]
scraper/image_downloader.py  →  download + exiftool → file_downloads

[chan pivot / background task]
pivot/resolver.py  →  per pending social_link / email / pgp
pivot/platforms/*.py  →  HTTP → PivotData (real_name, email, location, accounts)
storage/repository.py  →  pivot_results

[chan archive / POST /archive/search]
scraper/archive_client.py  →  4plebs / desuarchive / warosu
storage/repository.py  →  archive_posts

[chan profile / GET /tripcodes/{trip}/profile]
analysis/tripcode_profiler.py  →  aggregate all DB data for trip
analysis/temporal_profiler.py  →  timezone inference
→ rich table (CLI) or JSON (API → React UI)
```

---

## Identity Signal Priority

| Signal | Source | Real Name Confidence |
|---|---|---|
| PGP fingerprint → keyserver UID | post body | Very High — UID = `Name <email>` |
| GitHub commit emails | GitHub API /events | High — author.name + email on commits |
| Keybase proofs | keybase.io API | High — cryptographically verified |
| Email → Gravatar | post body/name field | Medium-High — display name often real |
| Email → HIBP | post body/name field | Medium — confirms real email |
| non-Anonymous name field | 4chan post | Medium — may be real |
| EXIF author/artist tag | downloaded image | Medium-High — set by photo software |
| EXIF GPS coords | downloaded image | Location only |
| Steam profile realname | steam URL in post | Medium — self-reported |
| Reddit profile | reddit URL in post | Low-Medium — pseudonymous |
| Tripcode → archive history | `chan archive --trip` | Context-dependent — may self-doxx |
| File MD5 cross-thread | `chan correlate` | Links posts, not name |
| Original filename | post metadata | Low — `john_cv.pdf` sometimes hits |
| Country code | geo-flag boards | Location only, country level |
| Poster ID | per-thread hash | Intra-thread only |

---

## Dependencies

**`requirements.txt` (Python):**
```
requests>=2.32
beautifulsoup4>=4.12
sqlalchemy>=2.0
pydantic-settings>=2.0
click>=8.1
rich>=13.0
python-dotenv>=1.0
fastapi>=0.111
uvicorn[standard]>=0.29
```

**Frontend (`frontend/package.json`):**
```
react, react-dom, typescript, vite
tailwindcss, @tailwindcss/vite
@tanstack/react-query
zustand
recharts
leaflet, react-leaflet
lucide-react
```

**External tools (must be on PATH):**
- `exiftool` — EXIF extraction. Install: https://exiftool.org

**Optional env vars:**
- `GITHUB_TOKEN` — raises GitHub API from 60 to 5000 req/hr
- `HIBP_API_KEY` — $3.50/mo, enables breach lookup

---

## Config (`.env.example`)

```
DB_PATH=chan_osint.db
IMAGE_DIR=data/images
REQUEST_DELAY=1.1
ARCHIVE_DELAY=2.0
PIVOT_DELAY=2.0
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Optional
GITHUB_TOKEN=
HIBP_API_KEY=
NOMINATIM_EMAIL=your@email.com
```

---

## Implementation Phases

Each phase = feature branch from `main` → PR → merge. Branch naming: `feat/phase-N-<name>`.

---

### Phase 1 — Core Infrastructure
**Branch:** `feat/phase-1-core-infra`

Files:
- `config/settings.py`
- `storage/engine.py`
- `storage/models.py` (all 8 tables)
- `storage/repository.py`
- `pyproject.toml`, `requirements.txt`, `.env.example`

Verify: `py -3.10 -c "from storage.engine import get_engine; get_engine()"`

---

### Phase 2 — Scraper Core
**Branch:** `feat/phase-2-scraper`

Files:
- `scraper/api_client.py`
- `scraper/post_parser.py`
- `scraper/link_extractor.py` (social + email + PGP)
- `tests/test_post_parser.py`
- `tests/test_link_extractor.py`
- `tests/fixtures/sample_thread.json`

Verify: `py -3.10 -m pytest tests/ -v`

---

### Phase 3 — CLI Core
**Branch:** `feat/phase-3-cli-core`

Files:
- `cli/main.py`
- `cli/commands/scrape.py`
- `cli/commands/show.py`
- `cli/commands/export.py`

Verify:
```
chan scrape "https://boards.4chan.org/g/thread/NNNNNN"
chan show threads
chan show links 1
chan export 1 --format json
```

---

### Phase 4 — Pivot Engine
**Branch:** `feat/phase-4-pivot-engine`

Files:
- `pivot/platforms/base.py`
- `pivot/platforms/github.py` (API + commit emails)
- `pivot/platforms/twitter.py`
- `pivot/platforms/telegram.py`
- `pivot/platforms/instagram.py`
- `pivot/platforms/reddit.py`
- `pivot/platforms/keybase.py`
- `pivot/platforms/pastebin.py`
- `pivot/platforms/steam.py`
- `pivot/platforms/email_pivot.py`
- `pivot/platforms/pgp_keyserver.py`
- `pivot/platforms/generic.py`
- `pivot/resolver.py`
- `cli/commands/pivot.py`

Verify:
```
chan pivot --platform github
chan pivot --platform email
chan show pivots 1
```

---

### Phase 5 — Image, EXIF & Thread Watcher
**Branch:** `feat/phase-5-images-exif`

Files:
- `scraper/image_downloader.py`
- `cli/commands/watch.py`

Verify:
```
chan scrape "https://boards.4chan.org/g/thread/NNNNNN" --download-images
chan watch "https://boards.4chan.org/pol/thread/NNNNNN" --interval 60
```
Requires `exiftool` on PATH.

---

### Phase 6 — Archive Integration
**Branch:** `feat/phase-6-archive`

Files:
- `scraper/archive_client.py` (4plebs → desuarchive → warosu)
- `cli/commands/archive.py`
- `tests/test_archive_client.py`

Verify:
```
chan archive --trip "!XXXXXXXX"
chan archive --md5 "BASE64=="
```

---

### Phase 7 — Analysis Layer
**Branch:** `feat/phase-7-analysis`

Files:
- `analysis/temporal_profiler.py`
- `analysis/tripcode_profiler.py`
- `analysis/md5_correlator.py`
- `cli/commands/profile.py`
- `cli/commands/correlate.py`

Verify:
```
chan profile --trip "!XXXXXXXX"
chan correlate --md5 "BASE64=="
```

---

### Phase 8 — Backend API
**Branch:** `feat/phase-8-backend-api`

Files:
- `api/main.py`
- `api/dependencies.py`
- `api/routes/threads.py`
- `api/routes/posts.py`
- `api/routes/links.py`
- `api/routes/emails.py`
- `api/routes/tripcodes.py`
- `api/routes/archive.py`
- `api/routes/correlate.py`
- `api/routes/scrape.py`
- `cli/commands/serve.py`

Verify:
```
chan serve
# GET http://localhost:8000/threads → JSON list
# POST http://localhost:8000/scrape {"url": "..."} → triggers scrape
# GET http://localhost:8000/tripcodes/!HASH/profile → profile JSON
```

---

### Phase 9 — Frontend Web UI
**Branch:** `feat/phase-9-frontend`

**Pre-implementation:** User provides design `.md` files with visual direction. Invoke `/frontend-design:frontend-design` and `/ui-ux-pro-max:ui-ux-pro-max` before writing any UI code to establish aesthetic, component design language, and layout patterns.

Files:
- Full `frontend/` directory (see architecture above)
- 8 pages: Dashboard, Threads, Thread, Tripcodes, Profile, Correlate, Archive, Images
- Typed API client (`frontend/src/api/`)
- Leaflet GPS map for geotagged EXIF images
- Activity heatmap (Recharts) on Profile page

Verify: `chan serve` → browser to `http://localhost:5173` → golden path through all 8 pages

---

### Phase 10 — Tests & Polish
**Branch:** `feat/phase-10-tests-polish`

Files:
- Remaining tests for archive, pivot, analysis
- `CLAUDE.md`
- README with screenshots

Verify: `py -3.10 -m pytest tests/ -v --tb=short`

---

## Full Verification (post all phases)

```powershell
cd d:\random_tools\chan-osint
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
py -3.10 -m pytest tests/ -v

chan scrape "https://boards.4chan.org/g/thread/NNNNNN" --download-images
chan show threads
chan show links 1
chan show emails 1
chan pivot --platform github
chan pivot --platform email
chan archive --trip "!XXXXXXXX"
chan correlate --md5 "BASE64=="
chan profile --trip "!XXXXXXXX"
chan export 1 --format json
chan serve   # → open http://localhost:5173
```
