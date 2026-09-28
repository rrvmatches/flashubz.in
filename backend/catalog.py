import math
import re
import os
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from core import db, Song, SongList, uid, now
from auth import sign, decode
from storage import cached_object

router = APIRouter(prefix='/api')
PUBLIC = {'published': True, 'is_deleted': {'$ne': True}}

@router.get('/songs', response_model=SongList)
async def songs(q: str = Query('', max_length=200), page: int = Query(1, ge=1), limit: int = Query(12, ge=1, le=48), sort: str = 'newest', ids: str = Query('', max_length=20000)):
    query = dict(PUBLIC)
    if q: query['$or'] = [{k:{'$regex':re.escape(q), '$options':'i'}} for k in ['name','artist','album','genre','language']]
    if ids: query['id'] = {'$in':ids.split(',')[:500]}
    total = await db.songs.count_documents(query)
    key, order = ('name', 1) if sort == 'az' else ('plays', -1) if sort == 'popular' else ('created_at', -1)
    result = await db.songs.find(query, {'_id':0}).sort(key,order).skip((page-1)*limit).limit(limit).to_list(limit)
    return {'songs':result, 'total':total, 'page':page, 'pages':math.ceil(total/limit)}

@router.get('/songs/{slug}', response_model=Song)
async def song(slug: str):
    result = await db.songs.find_one({**PUBLIC, 'slug':slug}, {'_id':0})
    if not result: raise HTTPException(404, 'Song not found')
    return result

@router.post('/songs/{song_id}/play')
async def play(song_id: str):
    result = await db.songs.update_one({**PUBLIC,'id':song_id}, {'$inc':{'plays':1}})
    if not result.matched_count: raise HTTPException(404, 'Song not found')
    await db.events.insert_one({'id':uid(), 'song_id':song_id,'type':'play','created_at':now()})
    return {'ok':True}

@router.post('/songs/{song_id}/download')
async def download(song_id: str):
    result = await db.songs.find_one({**PUBLIC,'id':song_id}, {'_id':0})
    if not result: raise HTTPException(404,'Song not found')
    if not result['download_enabled']: raise HTTPException(403, 'Downloads are not authorized for this song')
    token = sign({'purpose':'download','song_id':song_id}, 120)
    return {'url':f"/api/download/{song_id}?token={token}"}

def file_chunks(path, start, end):
    with path.open('rb') as f:
        f.seek(start)
        remaining = end-start+1
        while remaining > 0:
            chunk = f.read(min(262144, remaining))
            if not chunk: break
            remaining -= len(chunk)
            yield chunk

async def media_response(file_id, request, filename=None):
    record = await db.files.find_one({'id':file_id,'is_deleted':False}, {'_id':0})
    if not record: raise HTTPException(404,'Media not found')
    try: path = await run_in_threadpool(cached_object, record)
    except Exception: raise HTTPException(503, 'Media is temporarily unavailable. Please try again.')
    size = path.stat().st_size
    start, end, status = 0, size-1, 200
    headers = {'Accept-Ranges':'bytes','Cache-Control':'private, max-age=120','X-Content-Type-Options':'nosniff'}
    range_header = request.headers.get('range')
    if range_header:
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
        if not match or not any(match.groups()): raise HTTPException(416, headers={'Content-Range':f'bytes */{size}'})
        a, b = match.groups()
        if not a: start = max(0,size-int(b))
        else: start, end = int(a), min(int(b),size-1) if b else size-1
        if start > end or start >= size: raise HTTPException(416,headers={'Content-Range':f'bytes */{size}'})
        status=206
        headers['Content-Range']=f'bytes {start}-{end}/{size}'
    headers['Content-Length']=str(end-start+1)
    if filename: headers['Content-Disposition']=f"attachment; filename*=UTF-8''{quote(filename)}"
    return StreamingResponse(file_chunks(path,start,end),status_code=status,media_type=record['content_type'],headers=headers)

@router.get('/media/{file_id}')
async def media(file_id: str, request: Request):
    result = await db.songs.find_one({**PUBLIC, '$or':[{'audio_file_id':file_id},{'cover_file_id':file_id}]},{'_id':0,'id':1})
    if not result:
        from auth import admin
        await admin(request)
    return await media_response(file_id,request)

@router.get('/download/{song_id}')
async def download_file(song_id: str, request: Request, token: str):
    payload=decode(token)
    if payload.get('purpose') != 'download' or payload.get('song_id') != song_id: raise HTTPException(403,'Invalid download link')
    result=await db.songs.find_one({**PUBLIC,'id':song_id,'download_enabled':True},{'_id':0})
    if not result: raise HTTPException(403,'Download no longer available')
    response = await media_response(result['audio_file_id'],request, result['name']+'.'+result['audio_format'].lower())
    await db.songs.update_one({'id':song_id},{'$inc':{'downloads':1}})
    await db.downloads.insert_one({'id':uid(),'song_id':song_id,'song_name':result['name'],'created_at':now()})
    return response

class Contact(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    email: EmailStr
    message: str = Field(min_length=10,max_length=5000)

@router.post('/contact', status_code=201)
async def contact(data: Contact):
    await db.messages.insert_one({**data.model_dump(),'id':uid(),'created_at':now(),'read':False})
    return {'message':'Message received. Thank you for reaching out to FLASHUBZ.'}

@router.get('/settings')
async def settings():
    result=await db.site_settings.find_one({'id':'main'},{'_id':0,'tiktok_profile_url':1})
    return result or {'tiktok_profile_url':''}

class FavoriteEvent(BaseModel):
    visitor_id: str = Field(min_length=20,max_length=100)
    song_id: str
    active: bool

@router.post('/favorites/activity')
async def favorite_event(data: FavoriteEvent):
    if not await db.songs.count_documents({**PUBLIC,'id':data.song_id}): raise HTTPException(404,'Song not found')
    query={'visitor_id':data.visitor_id,'song_id':data.song_id}
    if data.active: await db.favorites.update_one(query,{'$set':{'created_at':now()}},upsert=True)
    else: await db.favorites.delete_one(query)
    return {'ok':True}