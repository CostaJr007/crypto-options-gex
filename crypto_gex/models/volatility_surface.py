"""Volatility Surface, Skew, and Smile Engine for Crypto Options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


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

    @classmethod
    def compute_skew_metrics(cls, df_chain: pd.DataFrame, spot: float) -> SkewMetrics:
        """Compute ATM vol and 25-Delta risk reversal skew."""
        df = df_chain.sort_values("strike").copy()
        df["dist_from_spot"] = np.abs(df["strike"] - spot)
        atm_row = df.loc[df["dist_from_spot"].idxmin()]
        atm_vol = float(atm_row["implied_vol"])

        # OTM Put strike (approx 10-15% below spot)
        otm_puts = df[df["strike"] < spot * 0.92]
        put_iv = float(otm_puts["implied_vol"].iloc[-1]) if not otm_puts.empty else atm_vol * 1.08

        # OTM Call strike (approx 10-15% above spot)
        otm_calls = df[df["strike"] > spot * 1.08]
        call_iv = float(otm_calls["implied_vol"].iloc[0]) if not otm_calls.empty else atm_vol * 1.03

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
