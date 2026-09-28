import os
import logging
from contextlib import asynccontextmanager
from xml.sax.saxutils import escape
from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from core import db, client
from auth import router as auth_router
from catalog import router as catalog_router
from admin_routes import router as admin_router
from storage import init_storage

@asynccontextmanager
async def lifespan(app):
    await db.songs.create_index('slug',unique=True)
    await db.songs.create_index([('published',1),('created_at',-1)])
    await db.songs.create_index('id',unique=True)
    await db.files.create_index('id',unique=True)
    await db.favorites.create_index([('visitor_id',1),('song_id',1)],unique=True)
    try: await run_in_threadpool(init_storage)
    except Exception as e: logging.error('Storage initialization failed: %s',type(e).__name__)
    yield
    client.close()

app=FastAPI(title='FLASHUBZ MUSIC WORLD',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[os.environ['PUBLIC_URL']],allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE','OPTIONS'],allow_headers=['Content-Type','Range','X-CSRF-Token'],expose_headers=['Content-Range','Accept-Ranges','Content-Length'])
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(admin_router)

@app.get('/api/')
async def health(): return {'name':'FLASHUBZ MUSIC WORLD','status':'ok'}

@app.get('/api/sitemap.xml')
async def sitemap():
    base=os.environ['PUBLIC_URL'].rstrip('/')
    urls=[base+p for p in ['/','/discover','/contact']]
    songs=await db.songs.find({'published':True,'is_deleted':False},{'_id':0,'slug':1}).to_list(50000)
    urls.extend(base+'/song/'+s['slug'] for s in songs)
    return Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(u)+'</loc></url>' for u in urls)+'</urlset>',media_type='application/xml')