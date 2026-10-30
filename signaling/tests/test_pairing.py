import asyncio

import pytest
from fastapi import HTTPException

from server import _new_pairing, _remove_expired_pairings, create_pairing, pairings


def test_pairing_payload_is_short_lived_and_scannable():
    pairings.clear()
    payload = _new_pairing("wss://remote.example/ws", now=1_000)

    assert payload["app"] == "nexus-remote"
    assert payload["v"] == 1
    assert payload["ws_url"] == "wss://remote.example/ws"
    assert payload["room"]
    assert len(payload["token"]) >= 40
    assert payload["expires_at"] == 1_180
    assert payload["room"] in pairings


def test_expired_pairings_are_removed():
    pairings.clear()
    payload = _new_pairing("wss://remote.example/ws", now=1_000)

    _remove_expired_pairings(now=1_179)
    assert payload["room"] in pairings

    _remove_expired_pairings(now=1_180)
    assert payload["room"] not in pairings


def test_pairing_api_requires_admin_token(monkeypatch):
    monkeypatch.delenv("NEXUS_PAIRING_ADMIN_TOKEN", raising=False)
    monkeypatch.setenv("NEXUS_PUBLIC_WSS_URL", "wss://remote.example/ws")

    with pytest.raises(HTTPException) as error:
        asyncio.run(create_pairing("Bearer wrong-token"))

    assert error.value.status_code == 503


def test_pairing_api_rejects_wrong_admin_token(monkeypatch):
    monkeypatch.setenv("NEXUS_PAIRING_ADMIN_TOKEN", "server-secret")
    monkeypatch.setenv("NEXUS_PUBLIC_WSS_URL", "wss://remote.example/ws")

    with pytest.raises(HTTPException) as error:
        asyncio.run(create_pairing("Bearer incorrect"))

    assert error.value.status_code == 401


def test_pairing_api_issues_new_session(monkeypatch):
    pairings.clear()
    monkeypatch.setenv("NEXUS_PAIRING_ADMIN_TOKEN", "server-secret")
    monkeypatch.setenv("NEXUS_PUBLIC_WSS_URL", "wss://remote.example/ws")

    payload = asyncio.run(create_pairing("Bearer server-secret"))

    assert payload["app"] == "nexus-remote"
    assert payload["ws_url"] == "wss://remote.example/ws"
    assert payload["room"] in pairings
    pairings.clear()
