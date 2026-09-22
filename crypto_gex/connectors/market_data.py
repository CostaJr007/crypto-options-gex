"""Market Data Connectors for Crypto Options (Binance / Deribit)."""

from __future__ import annotations

import math
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import requests
from ..models.greeks import CryptoGreeksEngine


class CryptoMarketData:
    """Provides market feeds and options chain generators for BTC and ETH."""

    @staticmethod
    def get_binance_spot(symbol: str = "BTCUSDT") -> float:
        """Fetch spot price from Binance."""
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        try:
            r = requests.get(url, timeout=4)
            if r.status_code == 200:
                return float(r.json()["price"])
        except Exception:
            pass
        return 65000.0 if "BTC" in symbol.upper() else 3500.0

    @staticmethod
    def generate_crypto_option_chain(
        spot: float = 65000.0,
        strikes_count: int = 21,
        time_to_maturity: float = 14.0 / 365.0,
        atm_vol: float = 0.55,
    ) -> pd.DataFrame:
        """Generate realistic crypto options chain with pronounced volatility smile and skew."""
        step = round(spot * 0.02, -2)  # 2% strike spacing
        center_strike = round(spot / 1000.0) * 1000.0
        strikes = [center_strike + (i - strikes_count // 2) * step for i in range(strikes_count)]

        records: List[Dict[str, float]] = []
        for K in strikes:
            moneyness = math.log(K / spot)
            # Crypto smile: high downside put skew + upside call convexity
            iv = max(0.20, atm_vol - 0.20 * moneyness + 0.8 * (moneyness ** 2))

            # Open interest distribution with dealer positioning (heavy call OI above, heavy put OI below)
            weight = math.exp(-0.5 * (moneyness / 0.12) ** 2)
            call_oi = max(10.0, round(500.0 * weight * (1.2 if K >= spot else 0.7)))
            put_oi = max(10.0, round(500.0 * weight * (1.3 if K <= spot else 0.6)))

            call_p = CryptoGreeksEngine.price("call", spot, K, time_to_maturity, 0.04, iv)
            put_p = CryptoGreeksEngine.price("put", spot, K, time_to_maturity, 0.04, iv)

            records.append({
                "strike": float(K),
                "time_to_maturity": float(time_to_maturity),
                "implied_vol": float(iv),
                "call_price": float(call_p),
                "put_price": float(put_p),
                "call_oi": float(call_oi),
                "put_oi": float(put_oi),
            })

        return pd.DataFrame(records)
