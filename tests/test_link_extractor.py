import pytest
from scraper.link_extractor import extract_from_post


def test_extracts_github_profile():
    data = extract_from_post("", "check my github at github.com/johndoe", "Anonymous")
    handles = [l["handle"] for l in data["links"] if l["platform"] == "github"]
    assert "johndoe" in handles


def test_rejects_twitter_non_profile():
    data = extract_from_post("", "go to twitter.com/home for updates", "Anonymous")
    assert not any(l["platform"] == "twitter" for l in data["links"])


def test_extracts_email_from_body():
    data = extract_from_post("", "contact me at john@example.org", "Anonymous")
    assert any(e["email"] == "john@example.org" for e in data["emails"])


def test_blocks_noreply_email():
    data = extract_from_post("", "noreply@company.com sent this", "Anonymous")
    assert not any(e["email"].startswith("noreply") for e in data["emails"])


def test_extracts_email_from_name_field():
    data = extract_from_post("", "", "John <john@protonmail.com>")
    assert any(e["source"] == "name_field" for e in data["emails"])


def test_pgp_requires_context():
    # 40-char hex without PGP context word → NOT extracted
    no_context = "A" * 40
    data = extract_from_post("", no_context, "Anonymous")
    assert len(data["pgp_fingerprints"]) == 0


def test_pgp_with_context():
    fp = "ABCD1234" * 5  # 40 chars
    data = extract_from_post("", f"my pgp fingerprint: {fp}", "Anonymous")
    assert any(p["fingerprint"] == fp for p in data["pgp_fingerprints"])


def test_composite_confidence():
    data = extract_from_post("", "keybase.io/janedoe", "Anonymous")
    link = next(l for l in data["links"] if l["platform"] == "keybase")
    assert link["confidence"] == pytest.approx(link["extraction_confidence"] * link["identity_weight"], abs=0.01)


def test_deduplication():
    # Same handle in both html and text → only one entry
    data = extract_from_post(
        '<a href="https://github.com/johndoe">github</a>',
        "github.com/johndoe",
        "Anonymous",
    )
    github_links = [l for l in data["links"] if l["platform"] == "github"]
    assert len(github_links) == 1
