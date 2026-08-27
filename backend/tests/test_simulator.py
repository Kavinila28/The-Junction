from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulator_missing_analysis():
    res = client.post("/api/analyses/nonexistent-id/simulate", json={"selected_interventions": ["pedestrian_signal"]})
    assert res.status_code == 404
