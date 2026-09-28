import os
import threading
from pathlib import Path
import requests

STORAGE_BASE = (os.environ.get('INTEGRATION_PROXY_URL') or '').strip() or 'https://integrations.emergentagent.com'
STORAGE_URL = STORAGE_BASE.rstrip('/') + '/objstore/api/v1/storage'
storage_key = None
lock = threading.Lock()
CACHE = Path('/tmp/flashubz-media-cache')
CACHE.mkdir(exist_ok=True)

def init_storage(force=False):
    global storage_key
    if storage_key and not force: return storage_key
    with lock:
        if storage_key and not force: return storage_key
        response = requests.post(f'{STORAGE_URL}/init', json={'emergent_key':os.environ['EMERGENT_LLM_KEY']}, timeout=30)
        response.raise_for_status()
        storage_key = response.json()['storage_key']
    return storage_key

def put_object(path, data, content_type):
    response = requests.put(f'{STORAGE_URL}/objects/{path}', headers={'X-Storage-Key':init_storage(), 'Content-Type':content_type}, data=data, timeout=120)
    response.raise_for_status()
    return response.json()

def cached_object(record):
    target = CACHE / record['id']
    if target.exists(): return target
    response = requests.get(f"{STORAGE_URL}/objects/{record['storage_path']}", headers={'X-Storage-Key':init_storage()}, timeout=120, stream=True)
    if response.status_code == 404:
        response.close()
        response = requests.get(f"{STORAGE_URL}/objects/{record['storage_path']}", headers={'X-Storage-Key':init_storage(force=True)}, timeout=120, stream=True)
    response.raise_for_status()
    import uuid
    temp = CACHE / str(uuid.uuid4())
    try:
        with temp.open('wb') as f:
            for chunk in response.iter_content(262144): f.write(chunk)
        temp.replace(target)
    finally:
        response.close()
        temp.unlink(missing_ok=True)
    files = sorted(CACHE.iterdir(), key=lambda p:p.stat().st_mtime)
    total = sum(p.stat().st_size for p in files)
    for file in files:
        if total < 512 * 1024 * 1024: break
        if file == target: continue
        total -= file.stat().st_size
        file.unlink(missing_ok=True)
    return target