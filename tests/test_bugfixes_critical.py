"""Regression tests for critical GEX / volatility-surface / IV fixes."""

import math

import numpy as np
import pandas as pd
from scipy.stats import norm

from crypto_gex.connectors.market_data import CryptoMarketData
from crypto_gex.models.gex import CryptoGammaExposureEngine
from crypto_gex.models.greeks import CryptoGreeksEngine
from crypto_gex.models.implied_vol import ImpliedVolatilitySolver
from crypto_gex.models.volatility_surface import VolatilitySurfaceEngine


def _delta(flag, S, K, T, r, q, sigma):
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    disc_q = math.exp(-q * T)
    if flag == "call":
        return disc_q * norm.cdf(d1)
    return disc_q * (norm.cdf(d1) - 1.0)


def test_iv_solver_supports_dividend_yield_q():
    # Price WITH q>0, solve passing q -> must recover true vol (calculated, not invented).
    S, K, T, r, q, true_vol = 65000.0, 70000.0, 14.0 / 365.0, 0.04, 0.03, 0.62
    for flag in ("call", "put"):
        px = CryptoGreeksEngine.price(flag, S, K, T, r, true_vol, q)
        solved = ImpliedVolatilitySolver.solve(px, flag, S, K, T, r, q)
        assert math.isclose(solved, true_vol, abs_tol=1e-5)
    # Default q=0 keeps backward compatibility.
    px0 = CryptoGreeksEngine.price("call", S, K, T, r, true_vol)
    assert math.isclose(ImpliedVolatilitySolver.solve(px0, "call", S, K, T, r), true_vol, abs_tol=1e-5)


def test_zero_gamma_uses_cumulative_not_single_strike():
    # Individual net_gex flips sign between strike 1 (+) and 2 (-),
    # but cumulative net GEX stays positive -> NO flip must be reported.
    # (net sign per strike == sign(call_oi - put_oi) since gamma > 0.)
    chain = pd.DataFrame({
        "strike": [90.0, 100.0, 110.0, 120.0],
        "time_to_maturity": [30.0 / 365.0] * 4,
        "implied_vol": [0.30] * 4,
        "call_oi": [1000.0, 100.0, 100.0, 100.0],
        "put_oi": [100.0, 200.0, 200.0, 200.0],
    })
    report = CryptoGammaExposureEngine.calculate(spot=100.0, df_chain=chain)
    nets = [s.net_gex for s in report.by_strike]
    assert nets[0] > 0 and nets[1] < 0  # single-strike flip exists (old logic would fire)
    cum = np.cumsum(np.array(nets))
    assert bool(np.all(cum > 0))  # cumulative never crosses
    assert report.zero_gamma_level is None


def test_zero_gamma_cumulative_interpolation():
    # Asymmetric chain: cumulative crosses between strikes 2 and 3.
    # Expected value recomputed from the report's own by_strike nets (calculated).
    chain = pd.DataFrame({
        "strike": [90.0, 100.0, 110.0],
        "time_to_maturity": [30.0 / 365.0] * 3,
        "implied_vol": [0.30] * 3,
        "call_oi": [50.0, 100.0, 800.0],
        "put_oi": [800.0, 100.0, 50.0],
    })
    report = CryptoGammaExposureEngine.calculate(spot=100.0, df_chain=chain)
    nets = [s.net_gex for s in report.by_strike]
    cum = list(np.cumsum(np.array(nets)))
    expected = None
    for i in range(len(cum) - 1):
        if (cum[i] <= 0 and cum[i + 1] >= 0) or (cum[i] >= 0 and cum[i + 1] <= 0):
            frac = abs(cum[i]) / abs(cum[i + 1] - cum[i])
            expected = report.by_strike[i].strike + frac * (
                report.by_strike[i + 1].strike - report.by_strike[i].strike
            )
            break
    assert expected is not None
    assert report.zero_gamma_level is not None
    assert math.isclose(report.zero_gamma_level, expected, rel_tol=1e-9)
    # Old single-strike logic would stop at the first per-strike sign change (100.0 here).
    assert not math.isclose(report.zero_gamma_level, 100.0, abs_tol=0.5)


def test_rr25d_uses_real_delta_strikes():
    spot = 65000.0
    r, q = 0.04, 0.0
    chain = CryptoMarketData.generate_crypto_option_chain(spot=spot)
    metrics = VolatilitySurfaceEngine.compute_skew_metrics(chain, spot=spot, r=r, q=q)

    df = chain.sort_values("strike")
    s = df["strike"].to_numpy(dtype=float)
    v = df["implied_vol"].to_numpy(dtype=float)
    T = float(np.median(df["time_to_maturity"].to_numpy(dtype=float)))

    def iv_at(K):
        return float(np.interp(float(K), s, v))

    # Independently re-solve |delta| = 0.25 in the test (calculated reference).
    from scipy.optimize import brentq
    disc_q = math.exp(-q * T)

    def call_f(K):
        sig = max(0.01, iv_at(K))
        d1 = (math.log(spot / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * math.sqrt(T))
        return disc_q * norm.cdf(d1) - 0.25

    def put_f(K):
        sig = max(0.01, iv_at(K))
        d1 = (math.log(spot / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * math.sqrt(T))
        return disc_q * (norm.cdf(d1) - 1.0) + 0.25

    kc = float(brentq(call_f, spot, spot * 3.0, xtol=1e-10))
    kp = float(brentq(put_f, spot * 0.2, spot, xtol=1e-10))
    assert math.isclose(_delta("call", spot, kc, T, r, q, iv_at(kc)), 0.25, abs_tol=1e-6)
    assert math.isclose(_delta("put", spot, kp, T, r, q, iv_at(kp)), -0.25, abs_tol=1e-6)

    ref_rr = iv_at(kc) - iv_at(kp)
    assert math.isclose(metrics.risk_reversal_25d, ref_rr, rel_tol=1e-6)
    assert math.isclose(metrics.call_skew_25d, iv_at(kc) - metrics.atm_volatility, rel_tol=1e-9)
    assert math.isclose(metrics.put_skew_25d, iv_at(kp) - metrics.atm_volatility, rel_tol=1e-9)

    # The solved strikes must differ from the old fixed +/-8% proxy strikes.
    assert abs(kc - spot * 1.08) > 1.0 or abs(kp - spot * 0.92) > 1.0
    old_call_iv = float(df[df["strike"] > spot * 1.08]["implied_vol"].iloc[0])
    old_put_iv = float(df[df["strike"] < spot * 0.92]["implied_vol"].iloc[-1])
    assert not math.isclose(metrics.risk_reversal_25d, old_call_iv - old_put_iv, rel_tol=1e-4)
