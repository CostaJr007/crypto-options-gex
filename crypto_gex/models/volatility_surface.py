"""Volatility Surface, Skew, and Smile Engine for Crypto Options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm


@dataclass(frozen=True)
class SkewMetrics:
    atm_volatility: float
    put_skew_25d: float  # 25-Delta Put IV minus ATM IV
    call_skew_25d: float # 25-Delta Call IV minus ATM IV
    risk_reversal_25d: float # Call 25d IV - Put 25d IV
    smile_curvature: float  # Butterfly / Straddle convexity


class VolatilitySurfaceEngine:
    """Analyzes and fits crypto volatility smile and skew dynamics."""

    @classmethod
    def fit_quadratic_smile(cls, strikes: np.ndarray, ivs: np.ndarray, spot: float) -> Tuple[float, float, float]:
        """Fit quadratic smile IV = a0 + a1*moneyness + a2*moneyness^2."""
        moneyness = np.log(strikes / spot)
        # Polyfit degree 2
        coeffs = np.polyfit(moneyness, ivs, deg=2)
        a2, a1, a0 = coeffs  # curvature, slope, level
        return float(a0), float(a1), float(a2)

    @staticmethod
    def _iv_interpolator(strikes: np.ndarray, ivs: np.ndarray):
        """Linear IV-in-strike interpolator (flat extrapolation outside range)."""
        s = np.asarray(strikes, dtype=float)
        v = np.asarray(ivs, dtype=float)
        order = np.argsort(s)
        s, v = s[order], v[order]

        def iv_at(k: float) -> float:
            return float(np.interp(float(k), s, v, left=float(v[0]), right=float(v[-1])))

        return iv_at

    @staticmethod
    def _d1(S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        return (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    @classmethod
    def _solve_25d_strike(
        cls,
        spot: float,
        T: float,
        r: float,
        q: float,
        iv_at,
        is_call: bool,
        atm_vol: float,
    ) -> Optional[float]:
        """Solve |delta(K)| = 0.25 for one side using Brent.

        Call: exp(-qT)*N(d1(K, sigma(K))) = 0.25  -> N(d1) = 0.25*exp(qT).
        Put:  exp(-qT)*(N(d1(K, sigma(K))) - 1) = -0.25 -> N(d1) = 1 - 0.25*exp(qT).
        sigma(K) comes from the chain IV interpolated in strike (this single
        solve with sigma(K) inside the objective is equivalent to converging
        the "nearest-strike IV, iterate 2-3x" procedure).
        """
        disc_q = float(np.exp(-q * T))

        def delta_minus_target(K: float) -> float:
            sig = max(0.01, float(iv_at(float(K))))
            d1 = cls._d1(spot, float(K), T, r, q, sig)
            if is_call:
                return float(disc_q * norm.cdf(d1) - 0.25)
            else:
                return float(disc_q * (norm.cdf(d1) - 1.0) + 0.25)

        try:
            if is_call:
                # OTM call: K > spot. f(spot) ~ +0.25..0.30 > 0, f(inf) -> -0.25 < 0.
                lo = float(spot)
                f_lo = delta_minus_target(lo)
                hi = float(spot * 1.5)
                f_hi = delta_minus_target(hi)
                expand = 0
                while not (f_hi < 0) and expand < 20:
                    hi = float(spot + (hi - spot) * 2.0)
                    if hi > spot * 20:
                        break
                    f_hi = delta_minus_target(hi)
                    expand += 1
                if not (f_lo > 0 and f_hi < 0):
                    return None
                return float(brentq(delta_minus_target, lo, hi, xtol=1e-8, maxiter=200))
            else:
                # OTM put: K < spot. f(spot) ~ -0.25 < 0, f(0+) -> +0.25 > 0.
                hi = float(spot)
                f_hi = delta_minus_target(hi)
                lo = float(spot * 0.5)
                f_lo = delta_minus_target(lo)
                expand = 0
                while not (f_lo > 0) and expand < 20:
                    lo = float(max(spot * 0.01, spot - (spot - lo) * 2.0))
                    if lo <= spot * 0.011:
                        f_lo = delta_minus_target(lo)
                        break
                    f_lo = delta_minus_target(lo)
                    expand += 1
                if not (f_lo > 0 and f_hi < 0):
                    return None
                return float(brentq(delta_minus_target, lo, hi, xtol=1e-8, maxiter=200))
        except Exception:
            return None

    @classmethod
    def compute_skew_metrics(
        cls,
        df_chain: pd.DataFrame,
        spot: float,
        r: float = 0.04,
        q: float = 0.0,
        T: Optional[float] = None,
    ) -> SkewMetrics:
        """Compute ATM vol and true 25-delta risk-reversal skew.

        For each side, solves ``|delta(K)| = 0.25`` via Black-Scholes
        (call: ``e^-qT*N(d1) = 0.25``; put: ``e^-qT*(N(d1)-1) = -0.25``)
        with ``brentq``, using the chain IV interpolated linearly in strike
        (flat extrapolation outside the quoted range). ``RR_25d`` is then
        ``IV(K_call25) - IV(K_put25)``. ``T`` defaults to the median of the
        chain ``time_to_maturity`` column.
        """
        df = df_chain.sort_values("strike").copy()
        df["dist_from_spot"] = np.abs(df["strike"] - spot)
        atm_row = df.loc[df["dist_from_spot"].idxmin()]
        atm_vol = float(atm_row["implied_vol"])

        strikes = df["strike"].to_numpy(dtype=float)
        ivs = df["implied_vol"].to_numpy(dtype=float)
        iv_at = cls._iv_interpolator(strikes, ivs)

        if T is None:
            if "time_to_maturity" in df.columns:
                T_eff = float(np.median(df["time_to_maturity"].to_numpy(dtype=float)))
            else:
                raise ValueError("Need 'time_to_maturity' column or explicit T for 25-delta solve.")
        else:
            T_eff = float(T)
        T_eff = max(1e-4, T_eff)

        k_call = cls._solve_25d_strike(spot, T_eff, r, q, iv_at, True, atm_vol)
        k_put = cls._solve_25d_strike(spot, T_eff, r, q, iv_at, False, atm_vol)

        if k_call is None:  # graceful fallback to old OTM proxy
            otm_calls = df[df["strike"] > spot * 1.08]
            call_iv = float(otm_calls["implied_vol"].iloc[0]) if not otm_calls.empty else atm_vol * 1.03
        else:
            call_iv = float(iv_at(k_call))

        if k_put is None:
            otm_puts = df[df["strike"] < spot * 0.92]
            put_iv = float(otm_puts["implied_vol"].iloc[-1]) if not otm_puts.empty else atm_vol * 1.08
        else:
            put_iv = float(iv_at(k_put))

        put_skew = put_iv - atm_vol
        call_skew = call_iv - atm_vol
        rr_25d = call_iv - put_iv
        butterfly = (call_iv + put_iv) / 2.0 - atm_vol

        return SkewMetrics(
            atm_volatility=atm_vol,
            put_skew_25d=put_skew,
            call_skew_25d=call_skew,
            risk_reversal_25d=rr_25d,
            smile_curvature=butterfly
        )
