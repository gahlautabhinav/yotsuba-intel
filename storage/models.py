from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from storage.engine import Base


class Thread(Base):
    __tablename__ = "threads"
    __table_args__ = (UniqueConstraint("board", "thread_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    board: Mapped[str] = mapped_column(Text, nullable=False)
    thread_no: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(Text)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    post_count: Mapped[Optional[int]] = mapped_column(Integer)
    unique_ips: Mapped[Optional[int]] = mapped_column(Integer)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_url: Mapped[Optional[str]] = mapped_column(Text)

    posts: Mapped[list[Post]] = relationship("Post", back_populates="thread")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("thread_id", "post_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(Integer, ForeignKey("threads.id"))
    post_no: Mapped[int] = mapped_column(Integer, nullable=False)
    resto: Mapped[int] = mapped_column(Integer, default=0)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    name: Mapped[Optional[str]] = mapped_column(Text, default="Anonymous")
    trip: Mapped[Optional[str]] = mapped_column(Text)
    poster_id: Mapped[Optional[str]] = mapped_column(Text)
    capcode: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(Text)
    country_name: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    has_file: Mapped[bool] = mapped_column(Boolean, default=False)
    filename: Mapped[Optional[str]] = mapped_column(Text)
    file_md5: Mapped[Optional[str]] = mapped_column(Text)
    file_ext: Mapped[Optional[str]] = mapped_column(Text)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    img_w: Mapped[Optional[int]] = mapped_column(Integer)
    img_h: Mapped[Optional[int]] = mapped_column(Integer)

    thread: Mapped[Thread] = relationship("Thread", back_populates="posts")
    social_links: Mapped[list[SocialLink]] = relationship("SocialLink", back_populates="post")
    emails: Mapped[list[Email]] = relationship("Email", back_populates="post")
    pgp_keys: Mapped[list[PgpKey]] = relationship("PgpKey", back_populates="post")
    file_downloads: Mapped[list[FileDownload]] = relationship("FileDownload", back_populates="post")


class SocialLink(Base):
    __tablename__ = "social_links"
    __table_args__ = (UniqueConstraint("post_id", "raw_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    raw_url: Mapped[str] = mapped_column(Text, nullable=False)
    handle: Mapped[Optional[str]] = mapped_column(Text)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    identity_weight: Mapped[float] = mapped_column(Float, default=0.3)
    confidence: Mapped[float] = mapped_column(Float, default=0.15)
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    post: Mapped[Post] = relationship("Post", back_populates="social_links")
    pivot_results: Mapped[list[PivotResult]] = relationship("PivotResult", back_populates="link")


class PivotResult(Base):
    __tablename__ = "pivot_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(Integer, ForeignKey("social_links.id"))
    status: Mapped[str] = mapped_column(Text, default="pending")
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    profile_data: Mapped[Optional[str]] = mapped_column(Text)
    raw_html_snippet: Mapped[Optional[str]] = mapped_column(Text)
    error: Mapped[Optional[str]] = mapped_column(Text)

    link: Mapped[SocialLink] = relationship("SocialLink", back_populates="pivot_results")


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (UniqueConstraint("post_id", "email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    email: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    pivoted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    breach_count: Mapped[Optional[int]] = mapped_column(Integer)
    breach_names: Mapped[Optional[str]] = mapped_column(Text)
    gravatar_url: Mapped[Optional[str]] = mapped_column(Text)
    real_name_hint: Mapped[Optional[str]] = mapped_column(Text)

    post: Mapped[Post] = relationship("Post", back_populates="emails")


class PgpKey(Base):
    __tablename__ = "pgp_keys"
    __table_args__ = (UniqueConstraint("post_id", "fingerprint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    key_id: Mapped[Optional[str]] = mapped_column(Text)
    real_name: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    keyserver_url: Mapped[Optional[str]] = mapped_column(Text)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    post: Mapped[Post] = relationship("Post", back_populates="pgp_keys")


class Tripcode(Base):
    __tablename__ = "tripcodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    trip_strength: Mapped[str] = mapped_column(Text, default="regular")
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    boards_seen: Mapped[Optional[str]] = mapped_column(Text)
    handles_found: Mapped[Optional[str]] = mapped_column(Text)
    emails_found: Mapped[Optional[str]] = mapped_column(Text)
    timezone_guess: Mapped[Optional[str]] = mapped_column(Text)
    timezone_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    timezone_histogram: Mapped[Optional[str]] = mapped_column(Text)
    timezone_warning: Mapped[Optional[str]] = mapped_column(Text)
    activity_periods: Mapped[Optional[str]] = mapped_column(Text)
    countries_seen: Mapped[Optional[str]] = mapped_column(Text)
    name_variants: Mapped[Optional[str]] = mapped_column(Text)
    stylometry_json: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)


class FileDownload(Base):
    __tablename__ = "file_downloads"
    __table_args__ = (UniqueConstraint("post_id", "file_md5"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    file_md5: Mapped[str] = mapped_column(Text, nullable=False)
    local_path: Mapped[Optional[str]] = mapped_column(Text)
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    exif_json: Mapped[Optional[str]] = mapped_column(Text)
    gps_lat: Mapped[Optional[float]] = mapped_column(Float)
    gps_lon: Mapped[Optional[float]] = mapped_column(Float)
    gps_location: Mapped[Optional[str]] = mapped_column(Text)
    camera_make: Mapped[Optional[str]] = mapped_column(Text)
    camera_model: Mapped[Optional[str]] = mapped_column(Text)
    software: Mapped[Optional[str]] = mapped_column(Text)
    author_tag: Mapped[Optional[str]] = mapped_column(Text)
    create_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    post: Mapped[Post] = relationship("Post", back_populates="file_downloads")


class Md5Correlation(Base):
    __tablename__ = "md5_correlations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_md5: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    board_count: Mapped[int] = mapped_column(Integer, default=0)
    has_tripcode_match: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    correlation_type: Mapped[Optional[str]] = mapped_column(Text)
    is_likely_meme: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text)
    computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class ArchivePost(Base):
    __tablename__ = "archive_posts"
    __table_args__ = (UniqueConstraint("source", "board", "post_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    board: Mapped[str] = mapped_column(Text, nullable=False)
    thread_no: Mapped[int] = mapped_column(Integer, nullable=False)
    post_no: Mapped[int] = mapped_column(Integer, nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    name: Mapped[Optional[str]] = mapped_column(Text)
    trip: Mapped[Optional[str]] = mapped_column(Text)
    poster_id: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(Text)
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    file_md5: Mapped[Optional[str]] = mapped_column(Text)
    filename: Mapped[Optional[str]] = mapped_column(Text)
    archive_url: Mapped[Optional[str]] = mapped_column(Text)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
