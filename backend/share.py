import io
import os
import re
import html
import hashlib
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from core import db
from storage import cached_object, CACHE

router=APIRouter(prefix='/api/share')
PUBLIC={'published':True,'is_deleted':{'$ne':True}}
ROOT=Path(__file__).parent
FONTS=ROOT/'fonts'
ARTWORK=ROOT/'assets'/'flashubz-artwork.webp'
BOT_RE=re.compile(r'facebookexternalhit|facebot|whatsapp|twitterbot|telegrambot|linkedinbot|discordbot|slackbot|instagram|tiktok|bytespider|pinterest|googlebot|bingbot|applebot|snapchat|redditbot|skypeuripreview|imessage|vkshare|embedly|quora|threads|preview|crawler|spider|bot',re.I)
RED=(228,35,62)
SILVER=(217,211,214)
PINK=(243,163,184,255)
MUTED=(200,180,190,255)

def base_url(): return os.environ['PUBLIC_URL'].rstrip('/')
def host(): return base_url().split('//')[-1]
def is_latin(text): return not re.search(r'[^\u0000-\u024F\u2000-\u206F]',text)

def font(name,size,weight=b'Bold'):
    f=ImageFont.truetype(str(FONTS/name),size)
    if '[' in name: f.set_variation_by_name(weight)
    return f

def display_font(text,size,condensed=True):
    if re.search(r'[\u0B80-\u0BFF]',text): return font('NotoSansTamil[wdth,wght].ttf',size)
    if not is_latin(text): return font('NotoSans[wdth,wght].ttf',size)
    return font('BarlowCondensed-Bold.ttf',size) if condensed else font('Manrope[wght].ttf',size,b'SemiBold')

def wrap(draw,text,f,max_width):
    lines,line=[],''
    for word in text.split():
        trial=(line+' '+word).strip()
        if draw.textlength(trial,font=f)<=max_width or not line: line=trial
        else: lines.append(line); line=word
    if line: lines.append(line)
    return lines

def fit_text(draw,text,max_width,max_lines,start,minimum):
    size=start
    while True:
        f=display_font(text,size); lines=wrap(draw,text,f,max_width)
        if (len(lines)<=max_lines and all(draw.textlength(l,font=f)<=max_width for l in lines)) or size<=minimum: break
        size-=4
    if len(lines)>max_lines:
        lines=lines[:max_lines]
        while draw.textlength(lines[-1]+'…',font=f)>max_width and len(lines[-1])>1: lines[-1]=lines[-1][:-1].rstrip()
        lines[-1]+='…'
    return f,lines,size

def line_height(f): a,de=f.getmetrics(); return int((a+de)*(0.86 if f.path.endswith('Bold.ttf') else 0.98))

def title_block(d,song,max_width,top,bottom,start,minimum,artist_h,pad):
    while True:
        f,lines,size=fit_text(d,title_text(song),max_width,2,start,minimum)
        y0=top+(pad[0] if f.path.endswith('Bold.ttf') else pad[1])
        if y0+len(lines)*line_height(f)+artist_h<=bottom or size<=minimum: return f,lines,y0
        start=size-4

def title_text(song): return song['name'].upper() if is_latin(song['name']) else song['name']

def cover_crop(im,w,h):
    scale=max(w/im.width,h/im.height); im=im.resize((round(im.width*scale),round(im.height*scale)),Image.LANCZOS)
    x=(im.width-w)//2; y=(im.height-h)//2
    return im.crop((x,y,x+w,y+h))

def rounded(im,radius):
    mask=Image.new('L',im.size,0); ImageDraw.Draw(mask).rounded_rectangle((0,0,im.width-1,im.height-1),radius,fill=255)
    out=im.convert('RGBA'); out.putalpha(mask); return out

def place_cover(card,cover,box,radius=22):
    x,y,w,h=box
    glow=Image.new('RGBA',card.size,(0,0,0,0)); ImageDraw.Draw(glow).rounded_rectangle((x-18,y-6,x+w+18,y+h+30),radius+14,fill=RED+(190,))
    card.alpha_composite(glow.filter(ImageFilter.GaussianBlur(34)))
    card.alpha_composite(rounded(cover_crop(cover.convert('RGB'),w,h),radius),(x,y))
    d=ImageDraw.Draw(card); d.rounded_rectangle((x,y,x+w-1,y+h-1),radius,outline=SILVER+(230,),width=3); d.rounded_rectangle((x+3,y+3,x+w-4,y+h-4),radius-3,outline=(40,10,18,200),width=1)

def waveform(d,x,y,width,height,seed,bars=44):
    digest=hashlib.sha256(seed.encode()).digest(); step=width/bars
    for i in range(bars):
        hgt=max(6,int((digest[i%32]/255)*height*(0.55+0.45*abs(((i*7)%bars)/bars-0.5)*2)))
        t=i/bars; color=(255-int(60*t),int(48+30*t),int(70+20*t))
        d.rounded_rectangle((x+i*step,y+(height-hgt)//2,x+i*step+step*0.55,y+(height+hgt)//2),2,fill=color)

def orb_crop(artwork): return artwork.crop((835,215,1285,665))

def landscape(song,cover,artwork):
    W,H=1200,630
    sx=W/artwork.width; oy=(round(artwork.height*sx)-H)//2
    card=ImageEnhance.Brightness(cover_crop(artwork,W,H)).enhance(0.42).filter(ImageFilter.GaussianBlur(1.2)).convert('RGBA')
    shade=Image.new('L',(W,H),0); sd=ImageDraw.Draw(shade)
    for i in range(0,700,4): sd.rectangle((i,0,i+4,H),fill=int(150*(1-i/700)))
    card.alpha_composite(Image.merge('RGBA',(Image.new('L',(W,H),0),)*3+(shade,)))
    lw,lh=int(580*sx),int(180*sx); lx,ly=int(70*sx),int(290*sx)-oy
    logo=artwork.crop((70,290,650,470)).resize((lw,lh),Image.LANCZOS).convert('RGBA')
    fade=Image.new('L',(lw,lh),0); ImageDraw.Draw(fade).rounded_rectangle((10,10,lw-10,lh-10),30,fill=255); logo.putalpha(fade.filter(ImageFilter.GaussianBlur(12)))
    card.alpha_composite(logo,(lx,ly))
    d=ImageDraw.Draw(card)
    d.text((66,ly-42),'NEW RELEASE  ·  FLASHUBZ MUSIC WORLD',font=font('Manrope[wght].ttf',19,b'Bold'),fill=PINK)
    f,lines,y=title_block(d,song,600,ly+lh,H-112,76,40,42,(4,14))
    for line in lines: d.text((66,y),line,font=f,fill=(255,255,255,255)); y+=line_height(f)
    d.text((66,y+8),song['artist'],font=display_font(song['artist'],28,condensed=False),fill=SILVER+(255,))
    waveform(d,66,H-98,400,40,song['slug'])
    if song.get('duration'): d.text((484,H-89),f"{int(song['duration']//60)}:{int(song['duration']%60):02d}",font=font('Manrope[wght].ttf',18,b'SemiBold'),fill=(140,110,125,255))
    d.text((66,H-46),'LISTEN NOW  →  '+host(),font=font('Manrope[wght].ttf',18,b'SemiBold'),fill=MUTED)
    if cover: place_cover(card,cover,(742,112,406,406))
    return card

def story(song,cover,artwork):
    W,H=1080,1920
    card=Image.new('RGBA',(W,H),(6,4,6,255))
    header=ImageEnhance.Brightness(cover_crop(artwork,W,640)).enhance(0.9).convert('RGBA')
    fade=Image.new('L',(W,640),255); fd=ImageDraw.Draw(fade)
    for i in range(300): fd.rectangle((0,340+i,W,341+i),fill=int(255*(1-i/300)))
    header.putalpha(fade); card.alpha_composite(header,(0,0))
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(glow).ellipse((-200,900,W+200,2100),fill=(120,10,30,150)); card.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    place_cover(card,cover or orb_crop(artwork),(180,560,720,720),radius=30)
    d=ImageDraw.Draw(card)
    label='NEW RELEASE  ·  FLASHUBZ MUSIC WORLD'; lf=font('Manrope[wght].ttf',26,b'Bold'); d.text(((W-d.textlength(label,font=lf))/2,1330),label,font=lf,fill=PINK)
    f,lines,y=title_block(d,song,920,1380,1672,100,52,56,(0,0))
    for line in lines: d.text(((W-d.textlength(line,font=f))/2,y),line,font=f,fill=(255,255,255,255)); y+=line_height(f)
    af=display_font(song['artist'],38,condensed=False); d.text(((W-d.textlength(song['artist'],font=af))/2,y+10),song['artist'],font=af,fill=SILVER+(255,))
    waveform(d,190,1690,700,56,song['slug'],bars=52)
    foot='LISTEN NOW  →  '+host()+'/song/'+song['slug']; ff=font('Manrope[wght].ttf',24,b'SemiBold')
    d.text(((W-d.textlength(foot,font=ff))/2,1800),foot,font=ff,fill=MUTED)
    return card

def render(kind,song,cover_record):
    artwork=Image.open(ARTWORK).convert('RGB')
    cover=None
    if cover_record:
        try: cover=Image.open(cached_object(cover_record)); cover.load()
        except Exception: cover=None
    card={'card':landscape,'story':story}[kind](song,cover,artwork) if song else cover_crop(artwork,1200,630).convert('RGBA')
    out=io.BytesIO(); card.convert('RGB').save(out,format='JPEG',quality=86,optimize=True,progressive=True); return out.getvalue()

def version(song): return hashlib.sha1('|'.join(str(song.get(k,'')) for k in ('name','artist','cover_file_id','duration')).encode()).hexdigest()[:10]

async def load_song(slug):
    song=await db.songs.find_one({**PUBLIC,'slug':slug},{'_id':0})
    if not song: raise HTTPException(404,'Song not found')
    return song

async def image(kind,song):
    target=CACHE/(f"share-{song['id']}-{kind}-{version(song)}.jpg" if song else 'share-brand.jpg')
    if not target.exists():
        cover_record=await db.files.find_one({'id':song['cover_file_id'],'is_deleted':False},{'_id':0}) if song and song.get('cover_file_id') else None
        target.write_bytes(await run_in_threadpool(render,kind,song,cover_record))
    return Response(target.read_bytes(),media_type='image/jpeg',headers={'Cache-Control':'public, max-age=86400','X-Content-Type-Options':'nosniff'})

@router.get('/brand.jpg')
async def brand_card(): return await image('card',None)

@router.get('/{slug}/card.jpg')
async def song_card(slug: str): return await image('card',await load_song(slug))

@router.get('/{slug}/story.jpg')
async def story_card(slug: str): return await image('story',await load_song(slug))

@router.get('/{slug}',response_class=HTMLResponse)
async def share_page(slug: str, request: Request):
    song=await load_song(slug); base=base_url(); e=html.escape
    title=f"{song['name']} — {song['artist']}"; description=song.get('description') or f"Listen to {song['name']} by {song['artist']} in the FLASHUBZ Music World. Independent sound. Limitless world."
    share_url=f"{base}/api/share/{slug}"; song_url=f"{base}/song/{slug}"; img=f"{base}/api/share/{slug}/card.jpg?v={version(song)}"
    bot=bool(BOT_RE.search(request.headers.get('user-agent','')))
    redirect='' if bot else f'<meta http-equiv="refresh" content="0;url={e(song_url)}"><script>location.replace({song_url!r})</script>'
    page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | FLASHUBZ MUSIC WORLD</title><meta name="description" content="{e(description)}">
<meta property="og:type" content="music.song"><meta property="og:site_name" content="FLASHUBZ MUSIC WORLD"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{e(share_url)}">
<meta property="og:image" content="{e(img)}"><meta property="og:image:secure_url" content="{e(img)}"><meta property="og:image:type" content="image/jpeg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(title)} — FLASHUBZ MUSIC WORLD">
<meta property="music:duration" content="{int(song.get('duration') or 0)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(description)}"><meta name="twitter:image" content="{e(img)}">
<link rel="canonical" href="{e(share_url)}">{redirect}
<style>body{{margin:0;background:#050305;color:#fff;font-family:Manrope,system-ui,sans-serif;text-align:center;padding:40px 20px}}img{{max-width:100%;width:720px;border-radius:6px;box-shadow:0 30px 80px #000}}a{{display:inline-block;margin-top:28px;background:#e4233e;color:#fff;text-decoration:none;font-weight:700;padding:14px 26px;border-radius:999px;letter-spacing:.08em}}p{{color:#b6adb1;font-size:14px}}</style></head>
<body><img src="{e(img)}" alt="{e(title)}"><p>{e(title)}</p><a href="{e(song_url)}">LISTEN IN FLASHUBZ MUSIC WORLD</a></body></html>'''
    return HTMLResponse(page,headers={'Cache-Control':'public, max-age=300'})
