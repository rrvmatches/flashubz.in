import io
import re
import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field, HttpUrl
from starlette.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from mutagen import File as AudioInfo
from core import db, uid, now, Song, SongEdit
from auth import admin
from storage import put_object, CACHE

router=APIRouter(prefix='/api/admin',dependencies=[Depends(admin)])

@router.get('/songs',response_model=list[Song])
async def admin_songs(): return await db.songs.find({'is_deleted':{'$ne':True}},{'_id':0}).sort('created_at',-1).to_list(5000)

async def store_file(data, original, content_type, kind, extension):
    file_id=uid()
    path=f"{os.environ['STORAGE_APP_NAME']}/music/{kind}/{file_id}.{extension}"
    try: result=await run_in_threadpool(put_object,path,data,content_type)
    except Exception: raise HTTPException(503,'Upload storage is temporarily unavailable. Please try again.')
    await db.files.insert_one({'id':file_id,'storage_path':result['path'],'original_filename':original,'content_type':content_type,'size':len(data),'is_deleted':False,'created_at':now()})
    return file_id

@router.post('/songs',response_model=Song,status_code=201)
async def upload_song(metadata: str=Form(...), audio: UploadFile=File(...), cover: UploadFile|None=File(None)):
    try: meta=SongEdit.model_validate_json(metadata)
    except Exception: raise HTTPException(422,'Please provide a song name, artist, and valid metadata.')
    ext=(audio.filename or '').rsplit('.',1)[-1].lower()
    mime={'mp3':'audio/mpeg','wav':'audio/wav','flac':'audio/flac','ogg':'audio/ogg','m4a':'audio/mp4'}
    if ext not in mime: raise HTTPException(422,'Supported audio: MP3, WAV, FLAC, OGG, M4A')
    data=await audio.read(100*1024*1024+1)
    if len(data)>100*1024*1024: raise HTTPException(413,'Audio must be smaller than 100 MB')
    try:
        info=AudioInfo(io.BytesIO(data))
        if info is None or not info.info.length: raise ValueError()
        duration=info.info.length
    except Exception: raise HTTPException(422,'This file is not valid audio')
    cover_bytes=None
    if cover and cover.filename:
        cover_bytes=await cover.read(10*1024*1024+1)
        if len(cover_bytes)>10*1024*1024: raise HTTPException(413,'Cover must be smaller than 10 MB')
        try:
            im=Image.open(io.BytesIO(cover_bytes)); im.load(); im.thumbnail((1200,1200))
            output=io.BytesIO(); im.convert('RGB').save(output,format='WEBP',quality=86); cover_bytes=output.getvalue()
        except Exception: raise HTTPException(422,'Please upload a valid cover image')
    audio_id=await store_file(data,audio.filename,mime[ext],'audio',ext)
    cover_id=await store_file(cover_bytes,cover.filename,'image/webp','covers','webp') if cover_bytes else ''
    base=re.sub(r'[^a-z0-9]+','-',meta.name.lower()).strip('-') or 'song'
    slug=base
    if await db.songs.count_documents({'slug':slug}): slug=base+'-'+uid()[:8]
    record={**meta.model_dump(),'id':uid(),'slug':slug,'audio_file_id':audio_id,'cover_file_id':cover_id,'audio_url':f'/api/media/{audio_id}','cover_url':f'/api/media/{cover_id}' if cover_id else '', 'duration':duration,'file_size':len(data),'audio_format':ext.upper(),'plays':0,'downloads':0,'is_deleted':False,'created_at':now()}
    await db.songs.insert_one(record.copy())
    await db.artists.update_one({'name':meta.artist},{'$setOnInsert':{'id':uid(),'created_at':now()}},upsert=True)
    if meta.album: await db.albums.update_one({'name':meta.album,'artist':meta.artist},{'$setOnInsert':{'id':uid()}},upsert=True)
    return Song(**record)

@router.put('/songs/{song_id}',response_model=Song)
async def edit_song(song_id: str,data: SongEdit):
    result=await db.songs.update_one({'id':song_id,'is_deleted':False},{'$set':data.model_dump()})
    if not result.matched_count: raise HTTPException(404,'Song not found')
    await db.artists.update_one({'name':data.artist},{'$setOnInsert':{'id':uid(),'created_at':now()}},upsert=True)
    return await db.songs.find_one({'id':song_id},{'_id':0})

@router.delete('/songs/{song_id}')
async def delete_song(song_id: str):
    song=await db.songs.find_one({'id':song_id,'is_deleted':False},{'_id':0})
    if not song: raise HTTPException(404,'Song not found')
    await db.songs.update_one({'id':song_id},{'$set':{'is_deleted':True,'published':False}})
    for fid in [song.get('audio_file_id'),song.get('cover_file_id')]:
        if fid:
            await db.files.update_one({'id':fid},{'$set':{'is_deleted':True}})
            (CACHE/fid).unlink(missing_ok=True)
    return {'ok':True}

@router.get('/dashboard')
async def dashboard():
    songs=await db.songs.find({'is_deleted':False},{'_id':0,'name':1,'id':1,'plays':1,'downloads':1,'published':1,'artist':1,'created_at':1}).sort('plays',-1).to_list(10000)
    days=[(datetime.now(timezone.utc)-timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6,-1,-1)]
    trend=[]
    for day in days:
        trend.append({'day':day[5:],'plays':await db.events.count_documents({'type':'play','created_at':{'$regex':'^'+day}}),'downloads':await db.downloads.count_documents({'created_at':{'$regex':'^'+day}})})
    return {'total_songs':len(songs),'published':sum(bool(s['published']) for s in songs),'total_plays':sum(s.get('plays',0) for s in songs),'total_downloads':await db.downloads.count_documents({}),'favorites':await db.favorites.count_documents({}),'popular':songs[:5],'recent':sorted(songs,key=lambda s:s['created_at'],reverse=True)[:5],'trend':trend,'messages':await db.messages.find({},{'_id':0}).sort('created_at',-1).to_list(50)}

class Settings(BaseModel):
    tiktok_profile_url: str = Field(default='',max_length=500)

@router.put('/settings')
async def settings(data: Settings):
    if data.tiktok_profile_url:
        from urllib.parse import urlparse
        url=urlparse(data.tiktok_profile_url)
        if url.scheme!='https' or url.hostname not in ('tiktok.com','www.tiktok.com','m.tiktok.com') or url.username or url.password:
            raise HTTPException(422,'Enter a valid HTTPS TikTok profile URL')
    await db.site_settings.update_one({'id':'main'},{'$set':data.model_dump()},upsert=True)
    return data.model_dump()

@router.get('/artists')
async def artists():
    return await db.songs.aggregate([{'$match':{'is_deleted':False}},{'$group':{'_id':'$artist','songs':{'$sum':1},'plays':{'$sum':'$plays'}}},{'$project':{'_id':0,'name':'$_id','songs':1,'plays':1}},{'$sort':{'name':1}}]).to_list(1000)

@router.get('/downloads')
async def downloads(): return await db.downloads.find({},{'_id':0}).sort('created_at',-1).to_list(200)

@router.get('/users')
async def users():
    return {'mode':'browser','accounts':0,'visitors_with_favorites':len(await db.favorites.distinct('visitor_id'))}

class EditorialPlaylist(BaseModel):
    name: str=Field(min_length=1,max_length=100)
    song_ids: list[str]=Field(default_factory=list,max_length=500)

@router.get('/playlists')
async def playlists(): return await db.playlists.find({},{'_id':0}).to_list(1000)

@router.post('/playlists',status_code=201)
async def create_playlist(data: EditorialPlaylist):
    record={**data.model_dump(),'id':uid(),'created_at':now()}
    await db.playlists.insert_one(record.copy())
    return record

@router.put('/playlists/{playlist_id}')
async def update_playlist(playlist_id: str,data: EditorialPlaylist):
    await db.playlists.update_one({'id':playlist_id},{'$set':data.model_dump()})
    return {'ok':True}

@router.delete('/playlists/{playlist_id}')
async def remove_playlist(playlist_id: str):
    await db.playlists.delete_one({'id':playlist_id})
    return {'ok':True}