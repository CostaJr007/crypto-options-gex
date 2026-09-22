"""Unit tests for crypto options and GEX models."""

import pytest
import math
from crypto_gex.models.greeks import CryptoGreeksEngine
from crypto_gex.models.gex import CryptoGammaExposureEngine
from crypto_gex.models.implied_vol import ImpliedVolatilitySolver
from crypto_gex.models.volatility_surface import VolatilitySurfaceEngine
from crypto_gex.connectors.market_data import CryptoMarketData


def test_crypto_greeks_put_call_parity():
    S, K, T, r, sigma = 65000.0, 65000.0, 30.0 / 365.0, 0.04, 0.55
    call_p = CryptoGreeksEngine.price("call", S, K, T, r, sigma)
    put_p = CryptoGreeksEngine.price("put", S, K, T, r, sigma)

    # Parity: C - P = S - K * exp(-r*T)
    left = call_p - put_p
    right = S - K * math.exp(-r * T)
    assert math.isclose(left, right, abs_tol=1e-3)


def test_crypto_gex_walls_and_zero_gamma():
    spot = 65000.0
    chain = CryptoMarketData.generate_crypto_option_chain(spot=spot, strikes_count=21)
    report = CryptoGammaExposureEngine.calculate(spot=spot, df_chain=chain, asset="BTC")

    assert report.asset == "BTC"
    assert report.spot_price == spot
    assert len(report.by_strike) == 21
    assert report.call_wall > 0
    assert report.put_wall > 0
    assert report.total_net_gex != 0


def test_crypto_implied_vol_solver():
    true_vol = 0.62
    S, K, T, r = 65000.0, 70000.0, 14.0 / 365.0, 0.04
    market_price = CryptoGreeksEngine.price("call", S, K, T, r, true_vol)

    solved = ImpliedVolatilitySolver.solve(market_price, "call", S, K, T, r)
    assert math.isclose(solved, true_vol, abs_tol=1e-5)


def test_volatility_surface_skew():
    chain = CryptoMarketData.generate_crypto_option_chain(spot=65000.0)
    metrics = VolatilitySurfaceEngine.compute_skew_metrics(chain, spot=65000.0)
    assert metrics.atm_volatility > 0
    assert metrics.smile_curvature > 0
