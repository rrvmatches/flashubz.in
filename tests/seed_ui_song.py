import json
from pathlib import Path

import requests
from dotenv import dotenv_values


front = dotenv_values("/app/frontend/.env")
back = dotenv_values("/app/backend/.env")
base = front["REACT_APP_BACKEND_URL"].rstrip("/")

fixtures = Path("/app/tests/fixtures")
audio = fixtures / "TEST_ONLY_tone_2.wav"
cover = fixtures / "TEST_ONLY_cover.png"

session = requests.Session()
login = session.post(
    f"{base}/api/admin/login",
    json={"username": back["ADMIN_USERNAME"], "password": back["ADMIN_PASSWORD"]},
    timeout=30,
)
login.raise_for_status()
session.headers['X-CSRF-Token'] = login.json()['csrf_token']

meta = {
    "name": "TEST_ONLY_UI_SEEDED_TRACK",
    "artist": "TEST_ONLY_ARTIST_UI",
    "album": "TEST_ONLY_ALBUM_UI",
    "genre": "TEST_ONLY_GENRE_UI",
    "language": "EN",
    "release_date": "2026-02-01",
    "lyrics": "[00:00.10]LINE 1\\n[00:00.60]LINE 2",
    "description": "TEST_ONLY seeded song for frontend checks",
    "download_enabled": True,
    "published": True,
}

with audio.open("rb") as a, cover.open("rb") as c:
    up = session.post(
        f"{base}/api/admin/songs",
        data={"metadata": json.dumps(meta)},
        files={"audio": (audio.name, a, "audio/wav"), "cover": (cover.name, c, "image/png")},
        timeout=120,
    )
up.raise_for_status()

song = up.json()
Path("/app/tests/last_seed_song_id.txt").write_text(song["id"])
print(f"seeded:{song['id']}:{song['slug']}")
