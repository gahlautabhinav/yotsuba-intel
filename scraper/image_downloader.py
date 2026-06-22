"""
Download 4chan thread images, extract EXIF metadata via exiftool,
and reverse-geocode any embedded GPS coordinates.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from config.settings import settings
from storage.repository import Repository

# Warn only once if exiftool is missing
_exiftool_warned = False


# ---------------------------------------------------------------------------
# GPS helpers
# ---------------------------------------------------------------------------

def _parse_gps(val) -> Optional[float]:
    """Parse an exiftool GPS string to decimal degrees.

    Accepts:
      - int / float  (already decimal)
      - "40 deg 42' 51.37\" N"  (exiftool verbose format)
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.search(r'(\d+)\s+deg\s+(\d+)\'\s+([\d.]+)"?\s*([NSEW])', str(val))
    if not m:
        return None
    deg, mins, secs, direction = m.groups()
    decimal = float(deg) + float(mins) / 60 + float(secs) / 3600
    if direction in ("S", "W"):
        decimal = -decimal
    return decimal


def _reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """Nominatim reverse geocode. Returns display_name or None."""
    time.sleep(1)  # Nominatim rate limit: 1 req/sec
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    ua = "yotsuba-intel/1.0"
    if settings.nominatim_email:
        ua = f"{ua} {settings.nominatim_email}"
    headers = {"User-Agent": ua}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("display_name")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# EXIF extraction
# ---------------------------------------------------------------------------

def _run_exiftool(path: str) -> dict:
    """Run exiftool -json on *path*. Returns parsed dict or {} on error."""
    global _exiftool_warned
    try:
        result = subprocess.run(
            ["exiftool", "-json", path],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {}
        data = json.loads(result.stdout)
        if isinstance(data, list) and data:
            return data[0]
        return {}
    except FileNotFoundError:
        if not _exiftool_warned:
            print(
                "[warning] exiftool not found on PATH — EXIF extraction skipped. "
                "Install from https://exiftool.org/"
            )
            _exiftool_warned = True
        return {}
    except Exception:
        return {}


def _extract_and_store_exif(path: str, file_md5: str, repo: Repository) -> None:
    """Run exiftool, parse EXIF fields, reverse-geocode GPS, save to DB."""
    exif = _run_exiftool(path)

    gps_lat = _parse_gps(exif.get("GPSLatitude"))
    gps_lon = _parse_gps(exif.get("GPSLongitude"))

    camera_make: Optional[str] = exif.get("Make")
    camera_model: Optional[str] = exif.get("Model")
    software: Optional[str] = exif.get("Software")
    author_tag: Optional[str] = (
        exif.get("Artist") or exif.get("Author") or exif.get("Creator")
    )

    # Parse CreateDate: "2023:01:15 14:30:00"
    create_date_dt: Optional[datetime] = None
    raw_date = exif.get("CreateDate")
    if raw_date:
        try:
            create_date_dt = datetime.strptime(str(raw_date), "%Y:%m:%d %H:%M:%S")
        except (ValueError, TypeError):
            pass

    gps_location: Optional[str] = None
    if gps_lat is not None and gps_lon is not None:
        gps_location = _reverse_geocode(gps_lat, gps_lon)

    repo.update_exif(
        file_md5=file_md5,
        exif_json=json.dumps(exif)[:50000],
        gps_lat=gps_lat,
        gps_lon=gps_lon,
        gps_location=gps_location,
        camera_make=camera_make,
        camera_model=camera_model,
        software=software,
        author_tag=author_tag,
        create_date=create_date_dt,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def download_thread_images(
    board: str,
    post_pairs: list[tuple[int, dict]],  # (post_db_id, PostData)
    repo: Repository,
) -> dict[str, int]:
    """Download all images in a thread.

    Args:
        board:       Board code, e.g. "g"
        post_pairs:  List of (post_db_id, PostData) tuples
        repo:        Repository instance

    Returns:
        {"downloaded": N, "skipped": N, "failed": N}
    """
    counts: dict[str, int] = {"downloaded": 0, "skipped": 0, "failed": 0}

    for post_db_id, pd in post_pairs:
        if not pd.get("has_file"):
            continue
        file_info = pd.get("file")
        if not file_info:
            continue

        file_md5: str = file_info["md5"]
        ext: str = file_info["ext"]
        tim: int = file_info["tim"]

        # Skip if already downloaded
        if repo.md5_already_downloaded(file_md5):
            counts["skipped"] += 1
            continue

        # Build URL and local path
        url = f"https://i.4cdn.org/{board}/{tim}{ext}"
        local_dir = Path(settings.image_dir) / board
        local_dir.mkdir(parents=True, exist_ok=True)
        # Sanitize base64 MD5 for use as a filename (replace / and + which are invalid)
        safe_md5 = file_md5.replace("/", "_").replace("+", "-").replace("=", "")
        local_path = str(local_dir / f"{safe_md5}{ext}")

        # Download
        try:
            resp = requests.get(url, timeout=15, stream=True)
            if resp.status_code != 200:
                print(f"[warning] Failed to download {url} (HTTP {resp.status_code})")
                counts["failed"] += 1
                time.sleep(0.5)
                continue

            with open(local_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
        except Exception as exc:
            print(f"[warning] Error downloading {url}: {exc}")
            counts["failed"] += 1
            time.sleep(0.5)
            continue

        # Save record and extract EXIF
        repo.save_file_download(post_db_id, file_md5, local_path)
        _extract_and_store_exif(local_path, file_md5, repo)

        counts["downloaded"] += 1
        time.sleep(0.5)  # Rate limit between downloads

    return counts
