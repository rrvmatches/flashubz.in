import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).parent / '.env')
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc).isoformat()

class Song(BaseModel):
    id: str
    name: str
    slug: str
    artist: str
    album: str = ''
    genre: str = ''
    language: str = ''
    release_date: str = ''
    duration: float = 0
    audio_url: str = ''
    cover_url: str = ''
    lyrics: str = ''
    description: str = ''
    download_enabled: bool = False
    published: bool = False
    created_at: str
    file_size: int = 0
    audio_format: str = 'MP3'
    plays: int = 0
    downloads: int = 0

class SongList(BaseModel):
    songs: list[Song]
    total: int
    page: int
    pages: int

class SongEdit(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    artist: str = Field(min_length=1, max_length=160)
    album: str = Field(default='', max_length=160)
    genre: str = Field(default='', max_length=80)
    language: str = Field(default='', max_length=80)
    release_date: str = ''
    lyrics: str = Field(default='', max_length=100000)
    description: str = Field(default='', max_length=5000)
    download_enabled: bool = False
    published: bool = False