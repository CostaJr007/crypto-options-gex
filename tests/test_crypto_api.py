"""Unit tests for Crypto FastAPI."""

from fastapi.testclient import TestClient
from crypto_gex.api.server import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "crypto-options-gex"


def test_greeks_endpoint():
    payload = {
        "flag": "call",
        "spot": 65000.0,
        "strike": 68000.0,
        "time_to_maturity": 0.038,
        "risk_free_rate": 0.04,
        "volatility": 0.55
    }
    res = client.post("/api/v1/greeks", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "price" in data
    assert "delta" in data
    assert 0 < data["delta"] < 1


def test_gex_endpoint():
    payload = {
        "asset": "BTC",
        "spot": 65000.0,
        "strikes_count": 15
    }
    res = client.post("/api/v1/gex", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["asset"] == "BTC"
    assert "call_wall" in data
    assert "put_wall" in data
