import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


@dataclass
class ScrapeJob:
    logs: list[str] = field(default_factory=list)
    done: bool = False
    error: Optional[str] = None

    def log(self, msg: str) -> None:
        self.logs.append(msg)


# In-memory job store — lives as long as the server process
JOBS: dict[str, ScrapeJob] = {}


class ScrapeRequest(BaseModel):
    url: str
    download_images: bool = False


@router.post("/")
def trigger_scrape(req: ScrapeRequest):
    """Trigger a scrape job and return a job_id for SSE streaming."""
    job_id = str(uuid.uuid4())
    job = ScrapeJob()
    JOBS[job_id] = job

    def _run():
        from scraper.api_client import ChanAPIClient
        from scraper.post_parser import parse_thread
        from scraper.link_extractor import extract_from_post
        from storage.engine import init_db
        from storage.repository import Repository
        from datetime import datetime

        init_db()
        client = ChanAPIClient()
        repo = Repository()
        try:
            job.log(f"→ parsing URL: {req.url}")
            board, thread_no = client.parse_thread_url(req.url)
            job.log(f"→ fetching /{board}/ #{thread_no} from 4chan API...")

            raw = client.get_thread(board, thread_no)
            if raw is None:
                job.log("✗ thread not found or deleted")
                job.done = True
                return

            thread_data, posts_data = parse_thread(board, raw)
            total = len(posts_data)
            job.log(f"✓ fetched {total} posts")

            job.log("→ saving thread to database...")
            thread = repo.save_thread(
                board=thread_data["board"],
                thread_no=thread_data["thread_no"],
                subject=thread_data.get("subject"),
                scraped_at=datetime.utcnow(),
                post_count=thread_data["post_count"],
                unique_ips=thread_data.get("unique_ips"),
                is_archived=thread_data.get("is_archived", False),
                raw_url=req.url,
            )
            job.log(f"✓ thread saved (db id={thread.id})")

            links_total = 0
            emails_total = 0
            trips_seen: set[str] = set()

            for i, pd in enumerate(posts_data, 1):
                post = repo.save_post(
                    thread_id=thread.id,
                    post_no=pd["post_no"],
                    resto=pd["resto"],
                    posted_at=pd["posted_at"],
                    name=pd["name"],
                    trip=pd.get("trip"),
                    poster_id=pd.get("poster_id"),
                    capcode=pd.get("capcode"),
                    country=pd.get("country"),
                    country_name=pd.get("country_name"),
                    body_html=pd.get("body_html"),
                    body_text=pd["body_text"],
                    has_file=pd["has_file"],
                    filename=pd["file"]["filename"] if pd["has_file"] and pd.get("file") else None,
                    file_md5=pd["file"]["md5"] if pd["has_file"] and pd.get("file") else None,
                    file_ext=pd["file"]["ext"] if pd["has_file"] and pd.get("file") else None,
                    file_size=pd["file"]["fsize"] if pd["has_file"] and pd.get("file") else None,
                    img_w=pd["file"]["w"] if pd["has_file"] and pd.get("file") else None,
                    img_h=pd["file"]["h"] if pd["has_file"] and pd.get("file") else None,
                )

                line = f"  [{i:>4}/{total}] post #{pd['post_no']}"
                if pd.get("trip"):
                    line += f"  trip={pd['trip']}"
                if pd["has_file"] and pd.get("file"):
                    line += f"  file={pd['file'].get('ext', '')}"
                job.log(line)

                if pd.get("trip"):
                    trip_str = pd["trip"]
                    strength = "secure" if trip_str.startswith("!!") else "regular"
                    repo.upsert_tripcode(trip_str, strength)
                    repo.update_tripcode_stats(
                        trip=trip_str, board=board, posted_at=pd["posted_at"],
                        country=pd.get("country"),
                        name=pd["name"] if pd["name"] != "Anonymous" else None,
                    )
                    if trip_str not in trips_seen:
                        trips_seen.add(trip_str)
                        job.log(f"        ↳ tripcode: {trip_str} ({strength})")

                extracted = extract_from_post(
                    body_html=pd.get("body_html") or "",
                    body_text=pd["body_text"],
                    name_field=pd["name"],
                )
                for lk in extracted["links"]:
                    repo.save_social_link(
                        post_id=post.id,
                        platform=lk["platform"],
                        raw_url=lk["raw_url"],
                        handle=lk["handle"],
                        extraction_confidence=lk["extraction_confidence"],
                        identity_weight=lk["identity_weight"],
                        confidence=lk["confidence"],
                    )
                    links_total += 1
                for email in extracted["emails"]:
                    repo.save_email(post_id=post.id, email=email["email"], source=email["source"])
                    emails_total += 1
                for pgp in extracted["pgp_fingerprints"]:
                    repo.save_pgp_key(post_id=post.id, fingerprint=pgp["fingerprint"])

                if extracted["links"] or extracted["emails"] or extracted["pgp_fingerprints"]:
                    signals = []
                    if extracted["links"]:
                        signals.append(f"{len(extracted['links'])} link(s)")
                    if extracted["emails"]:
                        signals.append(f"{len(extracted['emails'])} email(s)")
                    if extracted["pgp_fingerprints"]:
                        signals.append(f"{len(extracted['pgp_fingerprints'])} pgp key(s)")
                    job.log(f"        ↳ signals: {', '.join(signals)}")

            job.log(f"")
            job.log(f"✓ done — {total} posts · {links_total} links · {emails_total} emails · {len(trips_seen)} tripcodes")
        except Exception as e:
            job.log(f"✗ error: {e}")
            job.error = str(e)
        finally:
            job.done = True

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return {"status": "started", "job_id": job_id, "url": req.url}


@router.get("/stream/{job_id}")
async def stream_scrape(job_id: str):
    """SSE endpoint — streams log lines for a running scrape job."""
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        job = JOBS[job_id]
        sent = 0
        while True:
            while sent < len(job.logs):
                line = job.logs[sent].replace("\n", " ")
                yield f"data: {line}\n\n"
                sent += 1
            if job.done:
                yield "event: done\ndata: complete\n\n"
                break
            await asyncio.sleep(0.15)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
