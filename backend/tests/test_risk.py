import pytest
from app.core.risk import compute_risk, risk_category

def test_risk_category():
    assert risk_category(10) == "LOW"
    assert risk_category(24) == "LOW"
    assert risk_category(25) == "MODERATE"
    assert risk_category(49) == "MODERATE"
    assert risk_category(50) == "HIGH"
    assert risk_category(74) == "HIGH"
    assert risk_category(75) == "CRITICAL"

def test_compute_risk_empty():
    res = compute_risk([], duration_s=30.0)
    assert res.score == 0
    assert res.category == "LOW"
    assert len(res.factors) > 0
