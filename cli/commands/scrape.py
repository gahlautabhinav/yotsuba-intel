from __future__ import annotations

from datetime import datetime

import click
from rich.console import Console

console = Console()


@click.command()
@click.argument("url")
@click.option("--download-images", is_flag=True, default=False)
def scrape(url: str, download_images: bool) -> None:
    """Scrape a 4chan thread and store all extracted data."""
    from scraper.api_client import ChanAPIClient
    from scraper.post_parser import parse_thread
    from scraper.link_extractor import extract_from_post
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    client = ChanAPIClient()
    repo = Repository()

    # 1. Parse URL
    try:
        board, thread_no = client.parse_thread_url(url)
    except ValueError as e:
        console.print(f"[red]Invalid URL:[/red] {e}")
        raise SystemExit(1)

    # 2. Fetch thread
    console.print(f"Fetching /{board}/thread/{thread_no} ...")
    raw = client.get_thread(board, thread_no)
    if raw is None:
        console.print("[red]Thread not found (404)[/red]")
        raise SystemExit(1)

    # 3. Parse
    thread_data, posts_data = parse_thread(board, raw)

    # 4. Save thread
    thread = repo.save_thread(
        board=thread_data["board"],
        thread_no=thread_data["thread_no"],
        subject=thread_data.get("subject"),
        scraped_at=datetime.utcnow(),
        post_count=thread_data["post_count"],
        unique_ips=thread_data.get("unique_ips"),
        is_archived=thread_data.get("is_archived", False),
        raw_url=url,
    )

    # 5. Save posts + extract signals
    new_posts = 0
    new_links = 0
    new_emails = 0
    new_pgp = 0
    post_pairs: list[tuple[int, dict]] = []  # (post_db_id, PostData) for image downloader

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
        post_pairs.append((post.id, pd))
        new_posts += 1

        # Upsert tripcode if present
        if pd.get("trip"):
            trip_str = pd["trip"]
            strength = "secure" if trip_str.startswith("!!") else "regular"
            repo.upsert_tripcode(trip_str, strength)
            repo.update_tripcode_stats(
                trip=trip_str,
                board=board,
                posted_at=pd["posted_at"],
                country=pd.get("country"),
                handle=None,
                email=None,
                name=pd["name"] if pd["name"] != "Anonymous" else None,
            )

        # Extract links, emails, PGP
        extracted = extract_from_post(
            body_html=pd.get("body_html") or "",
            body_text=pd["body_text"],
            name_field=pd["name"],
        )

        for link in extracted["links"]:
            repo.save_social_link(
                post_id=post.id,
                platform=link["platform"],
                raw_url=link["raw_url"],
                handle=link["handle"],
                extraction_confidence=link["extraction_confidence"],
                identity_weight=link["identity_weight"],
                confidence=link["confidence"],
            )
            new_links += 1

        for email in extracted["emails"]:
            repo.save_email(post_id=post.id, email=email["email"], source=email["source"])
            new_emails += 1

        for pgp in extracted["pgp_fingerprints"]:
            repo.save_pgp_key(post_id=post.id, fingerprint=pgp["fingerprint"])
            new_pgp += 1

    if download_images:
        from scraper.image_downloader import download_thread_images
        dl_counts = download_thread_images(
            board=board,
            post_pairs=post_pairs,
            repo=repo,
        )
        console.print(
            f"Images: {dl_counts['downloaded']} downloaded, "
            f"{dl_counts['skipped']} skipped, "
            f"{dl_counts['failed']} failed"
        )

    # 6. Summary output
    console.print(
        f"[green]Done.[/green] Thread #{thread.id} | "
        f"{new_posts} posts | {new_links} links | "
        f"{new_emails} emails | {new_pgp} PGP keys"
    )
