"""Final cleanup assertions for public library and public settings state."""

from dotenv import dotenv_values
import requests


FRONTEND_ENV = dotenv_values('/app/frontend/.env')
BASE_URL = FRONTEND_ENV.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_public_song_library_is_empty_after_cleanup():
    assert BASE_URL, 'REACT_APP_BACKEND_URL missing in /app/frontend/.env'
    response = requests.get(f'{BASE_URL}/api/songs', timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 0
    assert isinstance(data['songs'], list)
    assert len(data['songs']) == 0


def test_tiktok_setting_is_empty_after_cleanup():
    assert BASE_URL, 'REACT_APP_BACKEND_URL missing in /app/frontend/.env'
    response = requests.get(f'{BASE_URL}/api/settings', timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data['tiktok_profile_url'] == ''
