#━━━━━━━━━❮Testes – Health Checks e Smoke❯━━━━━━━━━
"""Testes de smoke para endpoints críticos (health, root)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_liveness():
    """GET /health retorna 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "service" in data


def test_health_readiness():
    """GET /health/ready verifica MongoDB."""
    resp = client.get("/health/ready")
    # 200 se mongo conectado, 503 se não
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "mongo" in data


def test_root():
    """GET / retorna info da API."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "online"
    assert "name" in data
    assert "version" in data
