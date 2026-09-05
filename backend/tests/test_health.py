"""
Minimal smoke test. Expand as real endpoints get logic worth testing —
this one exists so `pytest` has something to run from commit one.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
