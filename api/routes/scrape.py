import threading
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ScrapeRequest(BaseModel):
    url: str
    download_images: bool = False


@router.post("/")
def trigger_scrape(req: ScrapeRequest):
    """Trigger a scrape job in a background thread."""
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
            board, thread_no = client.parse_thread_url(req.url)
            raw = client.get_thread(board, thread_no)
            if raw is None:
                return
            thread_data, posts_data = parse_thread(board, raw)
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
            for pd in posts_data:
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
                if pd.get("trip"):
                    trip_str = pd["trip"]
                    strength = "secure" if trip_str.startswith("!!") else "regular"
                    repo.upsert_tripcode(trip_str, strength)
                    repo.update_tripcode_stats(
                        trip=trip_str, board=board, posted_at=pd["posted_at"],
                        country=pd.get("country"),
                        name=pd["name"] if pd["name"] != "Anonymous" else None,
                    )
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
                for email in extracted["emails"]:
                    repo.save_email(post_id=post.id, email=email["email"], source=email["source"])
                for pgp in extracted["pgp_fingerprints"]:
                    repo.save_pgp_key(post_id=post.id, fingerprint=pgp["fingerprint"])
        except Exception as e:
            print(f"[scrape background] Error: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return {"status": "started", "url": req.url}
