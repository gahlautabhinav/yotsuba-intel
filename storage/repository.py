from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from storage.engine import get_session
from storage import models


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _json_append_unique(existing_json: Optional[str], value: Optional[str]) -> str:
    if not value:
        return existing_json or "[]"
    lst: list = json.loads(existing_json) if existing_json else []
    if value not in lst:
        lst.append(value)
    return json.dumps(lst)


class Repository:
    # ------------------------------------------------------------------
    # Thread methods
    # ------------------------------------------------------------------

    def save_thread(
        self,
        board: str,
        thread_no: int,
        subject: Optional[str] = None,
        scraped_at: Optional[datetime] = None,
        post_count: Optional[int] = None,
        unique_ips: Optional[int] = None,
        is_archived: bool = False,
        raw_url: Optional[str] = None,
    ) -> models.Thread:
        with get_session() as session:
            obj = (
                session.query(models.Thread)
                .filter_by(board=board, thread_no=thread_no)
                .first()
            )
            if obj is None:
                obj = models.Thread(board=board, thread_no=thread_no)
                session.add(obj)
            obj.subject = subject
            obj.scraped_at = scraped_at
            obj.post_count = post_count
            obj.unique_ips = unique_ips
            obj.is_archived = is_archived
            obj.raw_url = raw_url
            session.commit()
            session.refresh(obj)
            return obj

    def get_thread(self, thread_id: int) -> Optional[models.Thread]:
        with get_session() as session:
            return session.get(models.Thread, thread_id)

    def get_thread_by_board_no(self, board: str, thread_no: int) -> Optional[models.Thread]:
        with get_session() as session:
            return (
                session.query(models.Thread)
                .filter_by(board=board, thread_no=thread_no)
                .first()
            )

    def list_threads(self) -> list[models.Thread]:
        with get_session() as session:
            return session.query(models.Thread).all()

    # ------------------------------------------------------------------
    # Post methods
    # ------------------------------------------------------------------

    def save_post(self, thread_id: int, post_no: int, **fields) -> models.Post:
        with get_session() as session:
            obj = (
                session.query(models.Post)
                .filter_by(thread_id=thread_id, post_no=post_no)
                .first()
            )
            if obj is None:
                obj = models.Post(thread_id=thread_id, post_no=post_no)
                session.add(obj)
            for k, v in fields.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return obj

    def get_posts_by_thread(self, thread_id: int) -> list[models.Post]:
        with get_session() as session:
            return session.query(models.Post).filter_by(thread_id=thread_id).all()

    def get_post(self, post_id: int) -> Optional[models.Post]:
        with get_session() as session:
            return session.get(models.Post, post_id)

    # ------------------------------------------------------------------
    # Social link methods
    # ------------------------------------------------------------------

    def save_social_link(
        self,
        post_id: int,
        platform: str,
        raw_url: str,
        handle: Optional[str] = None,
        extraction_confidence: float = 0.5,
        identity_weight: float = 0.3,
        confidence: float = 0.15,
    ) -> models.SocialLink:
        with get_session() as session:
            obj = (
                session.query(models.SocialLink)
                .filter_by(post_id=post_id, raw_url=raw_url)
                .first()
            )
            if obj is None:
                obj = models.SocialLink(post_id=post_id, raw_url=raw_url)
                session.add(obj)
            obj.platform = platform
            obj.handle = handle
            obj.extraction_confidence = extraction_confidence
            obj.identity_weight = identity_weight
            obj.confidence = confidence
            obj.extracted_at = _utcnow()
            session.commit()
            session.refresh(obj)
            return obj

    def get_pending_links(self, platform: Optional[str] = None) -> list[models.SocialLink]:
        with get_session() as session:
            pivoted_ids = select(models.PivotResult.link_id).where(
                models.PivotResult.status.in_(["success", "failed", "blocked", "no_content"])
            )
            q = session.query(models.SocialLink).filter(
                models.SocialLink.id.not_in(pivoted_ids)
            )
            if platform:
                q = q.filter(models.SocialLink.platform == platform)
            return q.all()

    def get_links_by_thread(self, thread_id: int) -> list[models.SocialLink]:
        with get_session() as session:
            return (
                session.query(models.SocialLink)
                .join(models.Post, models.SocialLink.post_id == models.Post.id)
                .filter(models.Post.thread_id == thread_id)
                .all()
            )

    # ------------------------------------------------------------------
    # Pivot result methods
    # ------------------------------------------------------------------

    def save_pivot_result(
        self,
        link_id: int,
        status: str = "pending",
        http_status: Optional[int] = None,
        profile_data: Optional[str] = None,
        raw_html_snippet: Optional[str] = None,
        error: Optional[str] = None,
    ) -> models.PivotResult:
        with get_session() as session:
            obj = models.PivotResult(
                link_id=link_id,
                status=status,
                fetched_at=_utcnow(),
                http_status=http_status,
                profile_data=profile_data,
                raw_html_snippet=raw_html_snippet,
                error=error,
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def update_pivot_status(self, link_id: int, status: str) -> None:
        with get_session() as session:
            obj = (
                session.query(models.PivotResult)
                .filter_by(link_id=link_id)
                .order_by(models.PivotResult.id.desc())
                .first()
            )
            if obj:
                obj.status = status
                session.commit()

    # ------------------------------------------------------------------
    # Email methods
    # ------------------------------------------------------------------

    def save_email(
        self,
        post_id: int,
        email: str,
        source: str,
    ) -> models.Email:
        with get_session() as session:
            obj = (
                session.query(models.Email)
                .filter_by(post_id=post_id, email=email)
                .first()
            )
            if obj is None:
                obj = models.Email(post_id=post_id, email=email, source=source)
                session.add(obj)
            else:
                obj.source = source
            session.commit()
            session.refresh(obj)
            return obj

    def get_emails_by_thread(self, thread_id: int) -> list[models.Email]:
        with get_session() as session:
            return (
                session.query(models.Email)
                .join(models.Post, models.Email.post_id == models.Post.id)
                .filter(models.Post.thread_id == thread_id)
                .all()
            )

    def get_pgp_keys_by_thread(self, thread_id: int) -> list[models.PgpKey]:
        with get_session() as session:
            return (
                session.query(models.PgpKey)
                .join(models.Post, models.PgpKey.post_id == models.Post.id)
                .filter(models.Post.thread_id == thread_id)
                .all()
            )

    def get_pivot_results_by_thread(self, thread_id: int) -> list[tuple[models.SocialLink, Optional[models.PivotResult]]]:
        with get_session() as session:
            rows = (
                session.query(models.SocialLink, models.PivotResult)
                .join(models.Post, models.SocialLink.post_id == models.Post.id)
                .outerjoin(models.PivotResult, models.PivotResult.link_id == models.SocialLink.id)
                .filter(models.Post.thread_id == thread_id)
                .all()
            )
            return rows

    def get_pending_emails(self) -> list[models.Email]:
        with get_session() as session:
            return session.query(models.Email).filter_by(pivoted_at=None).all()

    def update_email_pivot(
        self,
        email_id: int,
        breach_count: Optional[int] = None,
        breach_names: Optional[str] = None,
        gravatar_url: Optional[str] = None,
        real_name_hint: Optional[str] = None,
    ) -> None:
        with get_session() as session:
            obj = session.get(models.Email, email_id)
            if obj:
                obj.breach_count = breach_count
                obj.breach_names = breach_names
                obj.gravatar_url = gravatar_url
                obj.real_name_hint = real_name_hint
                obj.pivoted_at = _utcnow()
                session.commit()

    # ------------------------------------------------------------------
    # PGP key methods
    # ------------------------------------------------------------------

    def save_pgp_key(
        self,
        post_id: int,
        fingerprint: str,
        key_id: Optional[str] = None,
    ) -> models.PgpKey:
        with get_session() as session:
            obj = (
                session.query(models.PgpKey)
                .filter_by(post_id=post_id, fingerprint=fingerprint)
                .first()
            )
            if obj is None:
                obj = models.PgpKey(post_id=post_id, fingerprint=fingerprint, key_id=key_id)
                session.add(obj)
            else:
                obj.key_id = key_id
            session.commit()
            session.refresh(obj)
            return obj

    def update_pgp_result(
        self,
        pgp_id: int,
        real_name: Optional[str] = None,
        email: Optional[str] = None,
        keyserver_url: Optional[str] = None,
    ) -> None:
        with get_session() as session:
            obj = session.get(models.PgpKey, pgp_id)
            if obj:
                obj.real_name = real_name
                obj.email = email
                obj.keyserver_url = keyserver_url
                obj.fetched_at = _utcnow()
                session.commit()

    def get_pending_pgp_keys(self) -> list[models.PgpKey]:
        with get_session() as session:
            return session.query(models.PgpKey).filter_by(fetched_at=None).all()

    # ------------------------------------------------------------------
    # Tripcode methods
    # ------------------------------------------------------------------

    def upsert_tripcode(self, trip: str, trip_strength: str = "regular") -> models.Tripcode:
        with get_session() as session:
            obj = session.query(models.Tripcode).filter_by(trip=trip).first()
            if obj is None:
                obj = models.Tripcode(trip=trip, trip_strength=trip_strength)
                session.add(obj)
            else:
                obj.trip_strength = trip_strength
            session.commit()
            session.refresh(obj)
            return obj

    def update_tripcode_stats(
        self,
        trip: str,
        board: str,
        posted_at: Optional[datetime] = None,
        country: Optional[str] = None,
        handle: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        with get_session() as session:
            obj = session.query(models.Tripcode).filter_by(trip=trip).first()
            if obj is None:
                return
            obj.post_count = (obj.post_count or 0) + 1
            obj.boards_seen = _json_append_unique(obj.boards_seen, board)
            obj.countries_seen = _json_append_unique(obj.countries_seen, country)
            obj.handles_found = _json_append_unique(obj.handles_found, handle)
            obj.emails_found = _json_append_unique(obj.emails_found, email)
            obj.name_variants = _json_append_unique(obj.name_variants, name)
            if posted_at:
                if obj.first_seen_at is None or posted_at < obj.first_seen_at:
                    obj.first_seen_at = posted_at
                if obj.last_seen_at is None or posted_at > obj.last_seen_at:
                    obj.last_seen_at = posted_at
            session.commit()

    def list_tripcodes(self) -> list[models.Tripcode]:
        with get_session() as session:
            return session.query(models.Tripcode).all()

    def get_tripcode(self, trip: str) -> Optional[models.Tripcode]:
        with get_session() as session:
            return session.query(models.Tripcode).filter_by(trip=trip).first()

    # ------------------------------------------------------------------
    # File download methods
    # ------------------------------------------------------------------

    def save_file_download(
        self,
        post_id: int,
        file_md5: str,
        local_path: Optional[str] = None,
    ) -> models.FileDownload:
        with get_session() as session:
            obj = (
                session.query(models.FileDownload)
                .filter_by(post_id=post_id, file_md5=file_md5)
                .first()
            )
            if obj is None:
                obj = models.FileDownload(
                    post_id=post_id,
                    file_md5=file_md5,
                    local_path=local_path,
                    downloaded_at=_utcnow(),
                )
                session.add(obj)
            else:
                obj.local_path = local_path
                obj.downloaded_at = _utcnow()
            session.commit()
            session.refresh(obj)
            return obj

    def update_exif(
        self,
        file_md5: str,
        exif_json: Optional[str] = None,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
        gps_location: Optional[str] = None,
        camera_make: Optional[str] = None,
        camera_model: Optional[str] = None,
        software: Optional[str] = None,
        author_tag: Optional[str] = None,
        create_date: Optional[datetime] = None,
    ) -> None:
        with get_session() as session:
            obj = session.query(models.FileDownload).filter_by(file_md5=file_md5).first()
            if obj:
                obj.exif_json = exif_json
                obj.gps_lat = gps_lat
                obj.gps_lon = gps_lon
                obj.gps_location = gps_location
                obj.camera_make = camera_make
                obj.camera_model = camera_model
                obj.software = software
                obj.author_tag = author_tag
                obj.create_date = create_date
                session.commit()

    def md5_already_downloaded(self, file_md5: str) -> bool:
        with get_session() as session:
            return (
                session.query(models.FileDownload)
                .filter_by(file_md5=file_md5)
                .first()
            ) is not None

    # ------------------------------------------------------------------
    # MD5 correlation methods
    # ------------------------------------------------------------------

    def save_md5_correlation(
        self,
        file_md5: str,
        post_count: int = 0,
        board_count: int = 0,
        has_tripcode_match: bool = False,
        confidence: float = 0.0,
        correlation_type: Optional[str] = None,
        is_likely_meme: bool = False,
        evidence_json: Optional[str] = None,
    ) -> models.Md5Correlation:
        with get_session() as session:
            obj = session.query(models.Md5Correlation).filter_by(file_md5=file_md5).first()
            if obj is None:
                obj = models.Md5Correlation(file_md5=file_md5)
                session.add(obj)
            obj.post_count = post_count
            obj.board_count = board_count
            obj.has_tripcode_match = has_tripcode_match
            obj.confidence = confidence
            obj.correlation_type = correlation_type
            obj.is_likely_meme = is_likely_meme
            obj.evidence_json = evidence_json
            obj.computed_at = _utcnow()
            session.commit()
            session.refresh(obj)
            return obj

    def get_md5_correlation(self, file_md5: str) -> Optional[models.Md5Correlation]:
        with get_session() as session:
            return session.query(models.Md5Correlation).filter_by(file_md5=file_md5).first()

    # ------------------------------------------------------------------
    # Archive post methods
    # ------------------------------------------------------------------

    def save_archive_post(
        self,
        source: str,
        board: str,
        thread_no: int,
        post_no: int,
        **fields,
    ) -> models.ArchivePost:
        with get_session() as session:
            obj = (
                session.query(models.ArchivePost)
                .filter_by(source=source, board=board, post_no=post_no)
                .first()
            )
            if obj is None:
                obj = models.ArchivePost(
                    source=source, board=board, thread_no=thread_no, post_no=post_no
                )
                session.add(obj)
            else:
                obj.thread_no = thread_no
            for k, v in fields.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return obj

    def get_archive_posts_by_trip(self, trip: str) -> list[models.ArchivePost]:
        with get_session() as session:
            return session.query(models.ArchivePost).filter_by(trip=trip).all()

    def get_archive_posts_by_md5(self, file_md5: str) -> list[models.ArchivePost]:
        with get_session() as session:
            return session.query(models.ArchivePost).filter_by(file_md5=file_md5).all()
