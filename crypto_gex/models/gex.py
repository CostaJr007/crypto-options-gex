"""Gamma Exposure (GEX) and Market Maker Positioning Engine for Crypto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd
from .greeks import CryptoGreeksEngine


@dataclass(frozen=True)
class StrikeGex:
    strike: float
    call_gex: float
    put_gex: float
    net_gex: float
    call_open_interest: float
    put_open_interest: float


@dataclass(frozen=True)
class GexReport:
    asset: str
    spot_price: float
    total_net_gex: float
    total_call_gex: float
    total_put_gex: float
    call_wall: float
    put_wall: float
    zero_gamma_level: Optional[float]
    regime: str  # "Long Gamma (Volatility Suppressed)" or "Short Gamma (Volatility Amplified)"
    by_strike: List[StrikeGex]


class CryptoGammaExposureEngine:
    """Calculates Option Market Maker Gamma Exposure across strikes for BTC and ETH."""

    @classmethod
    def calculate(
        cls,
        spot: float,
        df_chain: pd.DataFrame,
        asset: str = "BTC",
        r: float = 0.04,
        contract_multiplier: float = 1.0,
    ) -> GexReport:
        """Calculate GEX from crypto options chain.

        Required DataFrame columns:
        - 'strike': float
        - 'time_to_maturity': float (years)
        - 'implied_vol': float (annualized)
        - 'call_oi': float (Call Open Interest in contracts/coins)
        - 'put_oi': float (Put Open Interest in contracts/coins)
        """
        required = {"strike", "time_to_maturity", "implied_vol", "call_oi", "put_oi"}
        missing = required - set(df_chain.columns)
        if missing:
            raise ValueError(f"Missing required columns in crypto chain: {missing}")

        strike_rows: List[StrikeGex] = []

        for _, row in df_chain.iterrows():
            K = float(row["strike"])
            T = max(1e-4, float(row["time_to_maturity"]))
            vol = max(0.01, float(row["implied_vol"]))
            call_oi = float(row["call_oi"])
            put_oi = float(row["put_oi"])

            # Compute Gamma
            greeks = CryptoGreeksEngine.greeks("call", spot, K, T, r, vol)
            gamma = greeks.gamma

            # Standard dealer GEX in Dollars per 1% move: S^2 * Gamma * 0.01 * OI
            # Customers net long calls -> dealer short gamma -> call_gex is positive dealer hedge
            call_gex = call_oi * gamma * (spot ** 2) * 0.01 * contract_multiplier
            put_gex = -put_oi * gamma * (spot ** 2) * 0.01 * contract_multiplier
            net_gex = call_gex + put_gex

            strike_rows.append(StrikeGex(
                strike=K,
                call_gex=call_gex,
                put_gex=put_gex,
                net_gex=net_gex,
                call_open_interest=call_oi,
                put_open_interest=put_oi
            ))

        strike_rows.sort(key=lambda x: x.strike)
        total_call_gex = sum(x.call_gex for x in strike_rows)
        total_put_gex = sum(x.put_gex for x in strike_rows)
        total_net_gex = total_call_gex + total_put_gex

        call_wall = max(strike_rows, key=lambda x: x.call_gex).strike if strike_rows else spot
        put_wall = min(strike_rows, key=lambda x: x.put_gex).strike if strike_rows else spot

        # Zero Gamma Flip Level
        zero_gamma = None
        for i in range(len(strike_rows) - 1):
            s1 = strike_rows[i]
            s2 = strike_rows[i + 1]
            if (s1.net_gex <= 0 and s2.net_gex >= 0) or (s1.net_gex >= 0 and s2.net_gex <= 0):
                denom = (s2.net_gex - s1.net_gex)
                if abs(denom) > 1e-9:
                    frac = abs(s1.net_gex) / abs(denom)
                    zero_gamma = s1.strike + frac * (s2.strike - s1.strike)
                else:
                    zero_gamma = s1.strike
                break

        regime = "Long Gamma (Mean-Reverting / Volatility Dampened)" if total_net_gex >= 0 else "Short Gamma (Trend-Chasing / Volatility Amplified)"

        return GexReport(
            asset=asset.upper(),
            spot_price=spot,
            total_net_gex=total_net_gex,
            total_call_gex=total_call_gex,
            total_put_gex=total_put_gex,
            call_wall=call_wall,
            put_wall=put_wall,
            zero_gamma_level=zero_gamma,
            regime=regime,
            by_strike=strike_rows
        )
