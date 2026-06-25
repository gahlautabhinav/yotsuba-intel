# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

Report security issues to: `ai@globalvoxinc.com`

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

Expected response time: 72 hours. You will receive acknowledgment and a timeline for a fix.

## Threat Model

This tool makes outbound HTTP requests to:

- `a.4cdn.org` — 4chan public JSON API
- Archive sites (4plebs, warosu, etc.)
- PGP keyservers
- GitHub API
- Gravatar API
- HIBP API

It does **not** accept inbound connections from untrusted sources beyond the local API server.

## Known Risks

### SSRF via URL Input

The scrape endpoint accepts a user-supplied URL and fetches it. This is intentional (scraping 4chan threads), but the API server should never be exposed to the public internet. Run it on localhost only.

### SQLite File

The database file contains scraped post content, extracted emails, social handles, and PGP fingerprints. Protect it like sensitive research data:

- Do not commit `chan_osint.db` to version control (it is gitignored)
- Apply filesystem permissions appropriate to your threat model
- Encrypt the database or the disk if handling sensitive investigations

### Dependencies

Keep dependencies updated. Known CVEs in any of the following are in scope for this policy:

- FastAPI / uvicorn
- SQLAlchemy
- requests / httpx
- BeautifulSoup4

Run `pip audit` periodically.

### API Key Exposure

If you configure API keys (HIBP, GitHub token) in `.env`, never commit that file. It is gitignored by default.

## Hardening for Production

This tool is designed for local research use. If you expose the API server beyond localhost:

1. Add authentication to all API endpoints
2. Restrict CORS origins
3. Run behind a reverse proxy with TLS
4. Apply rate limiting to the `/scrape/` endpoint
5. Validate and sanitize all user-supplied URLs before fetching
