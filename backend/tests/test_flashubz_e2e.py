"""E2E API regression for auth, songs, media streaming, downloads, settings, and cleanup."""

import json
import os
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient


FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BACKEND_ENV = dotenv_values("/app/backend/.env")
BASE_URL = FRONTEND_ENV.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    return session


@pytest.fixture(scope="session")
def state():
    return {"songs": [], "message_ids": [], "playlist_ids": [], "fixture_dir": "/app/tests/fixtures"}


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_all(state):
    yield
    username = BACKEND_ENV.get("ADMIN_USERNAME")
    password = BACKEND_ENV.get("ADMIN_PASSWORD")
    if not (BASE_URL and username and password):
        return

    session = requests.Session()
    login = session.post(f"{BASE_URL}/api/admin/login", json={"username": username, "password": password}, timeout=30)
    if login.status_code == 200:
        session.headers['X-CSRF-Token'] = login.json()['csrf_token']
        for sid in state["songs"]:
            session.delete(f"{BASE_URL}/api/admin/songs/{sid}", timeout=30)

    mongo_url = BACKEND_ENV.get("MONGO_URL", "").strip('"')
    db_name = BACKEND_ENV.get("DB_NAME", "").strip('"')
    if mongo_url and db_name:
        client = MongoClient(mongo_url)
        db = client[db_name]
        song_ids = [sid for sid in state["songs"] if sid]
        db.messages.delete_many({"name": {"$regex": "^TEST_ONLY_"}})
        db.playlists.delete_many({"name": {"$regex": "^TEST_ONLY_"}})
        if song_ids:
            db.events.delete_many({"song_id": {"$in": song_ids}})
            db.downloads.delete_many({"song_id": {"$in": song_ids}})
            db.favorites.delete_many({"song_id": {"$in": song_ids}})
        client.close()


def _require_base_url():
    if not BASE_URL:
        pytest.fail("REACT_APP_BACKEND_URL missing in /app/frontend/.env")


def _admin_login(session: requests.Session):
    username = BACKEND_ENV.get("ADMIN_USERNAME")
    password = BACKEND_ENV.get("ADMIN_PASSWORD")
    assert username and password
    response = session.post(
        f"{BASE_URL}/api/admin/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    if response.status_code == 200:
        session.headers['X-CSRF-Token'] = response.json()['csrf_token']
    return response


def _song_metadata(name: str, *, published: bool, download_enabled: bool, lyrics: str = ""):
    return {
        "name": name,
        "artist": "TEST_ONLY_ARTIST",
        "album": "TEST_ONLY_ALBUM",
        "genre": "TEST_ONLY_GENRE",
        "language": "EN",
        "release_date": "2026-02-01",
        "lyrics": lyrics,
        "description": "TEST_ONLY_DESCRIPTION",
        "download_enabled": download_enabled,
        "published": published,
    }


def test_health_endpoint():
    _require_base_url()
    response = requests.get(f"{BASE_URL}/api/", timeout=20)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "FLASHUBZ" in data["name"]


def test_admin_me_unauth_returns_401():
    _require_base_url()
    response = requests.get(f"{BASE_URL}/api/admin/me", timeout=20)
    assert response.status_code == 401
    assert "Administrator sign-in required" in response.text


def test_admin_login_wrong_then_right_sets_secure_cookie(api_client):
    _require_base_url()
    bad = api_client.post(
        f"{BASE_URL}/api/admin/login",
        json={"username": "wrong", "password": "wrong"},
        timeout=30,
    )
    assert bad.status_code == 401

    good = _admin_login(api_client)
    assert good.status_code == 200
    assert "username" in good.json()
    cookie = good.headers.get("set-cookie", "")
    assert "flashubz_admin" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    # Preview ingress can isolate cookies using CHIPS instead of Strict.
    lower = cookie.lower()
    assert 'samesite=strict' in lower or ('samesite=none' in lower and 'partitioned' in lower)
    assert good.json().get('csrf_token')

    me = api_client.get(f"{BASE_URL}/api/admin/me", timeout=30)
    assert me.status_code == 200
    assert "username" in me.json()


def test_admin_logout_invalidates_session(api_client):
    _require_base_url()
    response = api_client.post(f"{BASE_URL}/api/admin/logout", timeout=20)
    assert response.status_code == 200
    me = api_client.get(f"{BASE_URL}/api/admin/me", timeout=20)
    assert me.status_code == 401


def test_upload_invalid_audio_rejected(api_client):
    _require_base_url()
    assert _admin_login(api_client).status_code == 200
    metadata = _song_metadata("TEST_ONLY_INVALID_AUDIO", published=True, download_enabled=False)
    files = {
        "audio": ("TEST_ONLY_invalid.wav", b"this is not real wav bytes", "audio/wav"),
    }
    response = api_client.post(
        f"{BASE_URL}/api/admin/songs",
        data={"metadata": json.dumps(metadata)},
        files=files,
        timeout=60,
    )
    assert response.status_code == 422
    assert "not valid audio" in response.text.lower()


def test_upload_published_song_and_stream_download_flow(api_client, state):
    _require_base_url()
    assert _admin_login(api_client).status_code == 200

    fixture_dir = Path(state["fixture_dir"])
    audio_path = fixture_dir / "TEST_ONLY_tone_1.wav"
    cover_path = fixture_dir / "TEST_ONLY_cover.png"
    assert audio_path.exists()
    assert cover_path.exists()

    metadata = _song_metadata(
        "TEST_ONLY_PUBLIC_TRACK",
        published=True,
        download_enabled=True,
        lyrics="[00:00.10]TEST ONLY LINE A\n[00:00.60]TEST ONLY LINE B",
    )

    with audio_path.open("rb") as audio_file, cover_path.open("rb") as cover_file:
        response = api_client.post(
            f"{BASE_URL}/api/admin/songs",
            data={"metadata": json.dumps(metadata)},
            files={
                "audio": (audio_path.name, audio_file, "audio/wav"),
                "cover": (cover_path.name, cover_file, "image/png"),
            },
            timeout=120,
        )

    assert response.status_code == 201
    data = response.json()
    state["songs"].append(data["id"])
    assert data["name"] == metadata["name"]
    assert data["published"] is True
    assert data["download_enabled"] is True
    assert data["slug"].startswith("test-only-public-track")
    assert data["cover_url"].startswith("/api/media/")

    listing = requests.get(f"{BASE_URL}/api/songs", timeout=30)
    assert listing.status_code == 200
    songs = listing.json()["songs"]
    assert any(s["id"] == data["id"] for s in songs)

    details = requests.get(f"{BASE_URL}/api/songs/{data['slug']}", timeout=30)
    assert details.status_code == 200
    assert details.json()["lyrics"].startswith("[00:00.10]")

    media = requests.get(f"{BASE_URL}{data['audio_url']}", headers={"Range": "bytes=0-999"}, timeout=30)
    assert media.status_code == 206
    assert media.headers.get("Content-Range", "").startswith("bytes 0-999/")
    assert media.headers.get("Accept-Ranges") == "bytes"

    signed = requests.post(f"{BASE_URL}/api/songs/{data['id']}/download", timeout=30)
    assert signed.status_code == 200
    download_url = signed.json()["url"]
    assert download_url.startswith("/api/download/")

    downloaded = requests.get(f"{BASE_URL}{download_url}", timeout=30)
    assert downloaded.status_code == 200
    assert downloaded.headers.get("Content-Disposition", "").startswith("attachment;")
    assert downloaded.headers.get("Content-Type", "").startswith("audio/")
    assert len(downloaded.content) > 100


def test_draft_song_hidden_and_disabled_download_rejected(api_client, state):
    _require_base_url()
    assert _admin_login(api_client).status_code == 200
    fixture_dir = Path(state["fixture_dir"])
    audio_path = fixture_dir / "TEST_ONLY_tone_2.wav"
    metadata = _song_metadata("TEST_ONLY_DRAFT_TRACK", published=False, download_enabled=False)

    with audio_path.open("rb") as audio_file:
        response = api_client.post(
            f"{BASE_URL}/api/admin/songs",
            data={"metadata": json.dumps(metadata)},
            files={"audio": (audio_path.name, audio_file, "audio/wav")},
            timeout=120,
        )
    assert response.status_code == 201
    song = response.json()
    state["songs"].append(song["id"])
    assert song["published"] is False

    listing = requests.get(f"{BASE_URL}/api/songs", params={"q": "TEST_ONLY_DRAFT_TRACK"}, timeout=30)
    assert listing.status_code == 200
    assert listing.json()["total"] == 0

    song_details = requests.get(f"{BASE_URL}/api/songs/{song['slug']}", timeout=30)
    assert song_details.status_code == 404

    denied = requests.post(f"{BASE_URL}/api/songs/{song['id']}/download", timeout=30)
    assert denied.status_code == 404


def test_contact_validation_and_success_and_settings_tiktok(api_client):
    _require_base_url()

    bad = requests.post(
        f"{BASE_URL}/api/contact",
        json={"name": "x", "email": "bad", "message": "short"},
        timeout=30,
    )
    assert bad.status_code == 422

    ok = requests.post(
        f"{BASE_URL}/api/contact",
        json={
            "name": "TEST_ONLY_CONTACT",
            "email": "test-only@example.com",
            "message": "TEST_ONLY message for admin inbox verification.",
        },
        timeout=30,
    )
    assert ok.status_code == 201
    assert "Message received" in ok.json()["message"]

    assert _admin_login(api_client).status_code == 200
    invalid = api_client.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": "https://example.com/not-tiktok"},
        timeout=30,
    )
    assert invalid.status_code == 422

    valid = api_client.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": "https://www.tiktok.com/@flashubz_test_only"},
        timeout=30,
    )
    assert valid.status_code == 200
    assert valid.json()["tiktok_profile_url"] == "https://www.tiktok.com/@flashubz_test_only"

    reset = api_client.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        timeout=30,
    )
    assert reset.status_code == 200
    assert reset.json()["tiktok_profile_url"] == ""


def test_sitemap_and_robots_policy():
    _require_base_url()
    sitemap = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=30)
    assert sitemap.status_code == 200
    assert "<urlset" in sitemap.text
    assert "/discover" in sitemap.text
    assert "/contact" in sitemap.text

    robots = requests.get(f"{BASE_URL}/robots.txt", timeout=30)
    assert robots.status_code == 200
    assert "Disallow: /admin" in robots.text
