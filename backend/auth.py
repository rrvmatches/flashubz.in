import os
import time
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel, Field
from core import db

router = APIRouter(prefix='/api/admin')
attempts = defaultdict(list)
class Login(BaseModel):
    username: str = Field(max_length=160)
    password: str = Field(max_length=200)

def sign(payload, seconds=28800):
    return jwt.encode({**payload, 'exp': datetime.now(timezone.utc) + timedelta(seconds=seconds)}, os.environ['SESSION_SECRET'], algorithm='HS256')

def decode(token):
    try: return jwt.decode(token, os.environ['SESSION_SECRET'], algorithms=['HS256'])
    except jwt.PyJWTError: raise HTTPException(401, 'Session expired. Please sign in again.')

async def admin(request: Request):
    token = request.cookies.get('flashubz_admin')
    payload = decode(token) if token else {}
    if payload.get('role') != 'admin':
        raise HTTPException(401, 'Administrator sign-in required')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        # A session-bound synchronizer token survives trusted proxy Origin rewriting.
        # Cross-site forms cannot supply it; cross-origin scripts cannot read /me.
        expected = payload.get('csrf', '')
        supplied = request.headers.get('x-csrf-token', '')
        if not expected or not secrets.compare_digest(expected, supplied):
            raise HTTPException(403, 'Please refresh your admin session and try again.')
    return payload

@router.post('/login')
async def login(data: Login, request: Request, response: Response):
    ip = request.client.host
    attempts[ip] = [t for t in attempts[ip] if t > time.time() - 300]
    if len(attempts[ip]) >= 10: raise HTTPException(429, 'Too many attempts. Try again in five minutes.')
    attempts[ip].append(time.time())
    valid = secrets.compare_digest(data.username, os.environ['ADMIN_USERNAME']) and secrets.compare_digest(data.password, os.environ['ADMIN_PASSWORD'])
    if not valid: raise HTTPException(401, 'Incorrect username or password')
    attempts[ip] = []
    csrf = secrets.token_urlsafe(32)
    response.set_cookie('flashubz_admin', sign({'role':'admin', 'csrf':csrf}), httponly=True, secure=True, samesite='strict', max_age=28800, path='/api')
    return {'username': data.username, 'csrf_token':csrf}

@router.get('/me')
async def me(session=Depends(admin)):
    if not session.get('csrf'): raise HTTPException(401, 'Please sign in again to refresh your session.')
    return {'username': os.environ['ADMIN_USERNAME'], 'csrf_token':session['csrf']}

@router.post('/logout', dependencies=[Depends(admin)])
async def logout(response: Response):
    response.delete_cookie('flashubz_admin', path='/api', secure=True, httponly=True, samesite='strict')
    return {'ok': True}