from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "THE JUNCTION API"

def test_meta():
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert "Predicting danger" in data["tagline"]

def test_list_analyses():
    res = client.get("/api/analyses")
    assert res.status_code == 200
    data = res.json()
    assert "analyses" in data
