from pathlib import Path

import requests
from dotenv import dotenv_values
from pymongo import MongoClient


front = dotenv_values("/app/frontend/.env")
back = dotenv_values("/app/backend/.env")
base = front["REACT_APP_BACKEND_URL"].rstrip("/")

session = requests.Session()
login = session.post(
    f"{base}/api/admin/login",
    json={"username": back["ADMIN_USERNAME"], "password": back["ADMIN_PASSWORD"]},
    timeout=30,
)
if login.status_code == 200:
    session.headers['X-CSRF-Token'] = login.json()['csrf_token']
    songs = session.get(f"{base}/api/admin/songs", timeout=30).json()
    for song in songs:
        if song.get("name", "").startswith("TEST_ONLY_") or song.get("artist", "").startswith("TEST_ONLY_"):
            session.delete(f"{base}/api/admin/songs/{song['id']}", timeout=30)

mongo = MongoClient(back["MONGO_URL"].strip('"'))
db = mongo[back["DB_NAME"].strip('"')]

song_ids = [s["id"] for s in db.songs.find({"name": {"$regex": "^TEST_ONLY_"}}, {"id": 1, "_id": 0})]
db.messages.delete_many({"name": {"$regex": "^TEST_ONLY_"}})
db.messages.delete_many({"message": {"$regex": "TEST_ONLY"}})
db.playlists.delete_many({"name": {"$regex": "^TEST_ONLY_"}})
if song_ids:
    db.events.delete_many({"song_id": {"$in": song_ids}})
    db.downloads.delete_many({"song_id": {"$in": song_ids}})
    db.favorites.delete_many({"song_id": {"$in": song_ids}})

mongo.close()
Path("/app/tests/last_seed_song_id.txt").unlink(missing_ok=True)
print("cleanup_complete")
