"""Admin auth + CSRF regression checks for protected non-GET routes."""

import os

import requests
from dotenv import dotenv_values


FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BACKEND_ENV = dotenv_values("/app/backend/.env")
BASE_URL = FRONTEND_ENV.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _require_base_url():
    assert BASE_URL, "REACT_APP_BACKEND_URL missing in /app/frontend/.env"


def _login(session: requests.Session):
    username = BACKEND_ENV.get("ADMIN_USERNAME")
    password = BACKEND_ENV.get("ADMIN_PASSWORD")
    assert username and password, "ADMIN credentials missing in /app/backend/.env"
    response = session.post(
        f"{BASE_URL}/api/admin/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    return response


def test_login_and_me_return_csrf_token():
    _require_base_url()
    session = requests.Session()

    login = _login(session)
    assert login.status_code == 200
    login_data = login.json()
    assert login_data.get("csrf_token")
    assert isinstance(login_data["csrf_token"], str)

    me = session.get(f"{BASE_URL}/api/admin/me", timeout=30)
    assert me.status_code == 200
    me_data = me.json()
    assert me_data.get("csrf_token")
    assert me_data["csrf_token"] == login_data["csrf_token"]


def test_protected_write_unauthenticated_returns_401():
    _require_base_url()
    response = requests.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        timeout=30,
    )
    assert response.status_code == 401


def test_protected_write_missing_csrf_returns_403():
    _require_base_url()
    session = requests.Session()
    login = _login(session)
    assert login.status_code == 200

    response = session.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        timeout=30,
    )
    assert response.status_code == 403


def test_protected_write_wrong_csrf_returns_403():
    _require_base_url()
    session = requests.Session()
    login = _login(session)
    assert login.status_code == 200

    session.headers["X-CSRF-Token"] = "definitely-wrong-csrf-token"
    response = session.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        timeout=30,
    )
    assert response.status_code == 403


def test_protected_write_with_other_sessions_csrf_returns_403():
    _require_base_url()
    session_a = requests.Session()
    session_b = requests.Session()

    login_a = _login(session_a)
    login_b = _login(session_b)
    assert login_a.status_code == 200
    assert login_b.status_code == 200

    csrf_from_b = login_b.json()["csrf_token"]
    session_a.headers["X-CSRF-Token"] = csrf_from_b
    response = session_a.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        timeout=30,
    )
    assert response.status_code == 403


def test_protected_write_with_valid_cookie_and_csrf_returns_200():
    _require_base_url()
    session = requests.Session()
    login = _login(session)
    assert login.status_code == 200

    csrf = login.json()["csrf_token"]
    session.headers["X-CSRF-Token"] = csrf
    response = session.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tiktok_profile_url"] == ""


def test_spoofed_origin_without_csrf_still_forbidden():
    _require_base_url()
    session = requests.Session()
    login = _login(session)
    assert login.status_code == 200

    response = session.put(
        f"{BASE_URL}/api/admin/settings",
        json={"tiktok_profile_url": ""},
        headers={"Origin": "https://evil.example"},
        timeout=30,
    )
    assert response.status_code == 403
