"""Implied Volatility Solver for Crypto Options."""

from __future__ import annotations

import math
from typing import Literal
from scipy.optimize import brentq
from .greeks import CryptoGreeksEngine


class ImpliedVolatilitySolver:
    """Solves for implied volatility on high-volatility crypto assets."""

    @classmethod
    def solve(
        cls,
        market_price: float,
        flag: Literal["call", "put"],
        S: float,
        K: float,
        T: float,
        r: float = 0.04,
        initial_guess: float = 0.50,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> float:
        if market_price <= 0:
            raise ValueError(f"Market price must be positive, got {market_price}")
        if T <= 0:
            raise ValueError(f"Time to maturity T must be positive, got {T}")

        is_call = (flag.lower() == "call")
        discount_r = math.exp(-r * T)

        intrinsic = max(0.0, (S - K * discount_r) if is_call else (K * discount_r - S))
        if market_price < intrinsic - tolerance:
            raise ValueError(
                f"Option price ({market_price}) is below intrinsic value ({intrinsic:.4f}). Arbitrage violation."
            )

        # 1. Newton-Raphson
        sigma = max(0.01, initial_guess)
        for _ in range(max_iterations):
            try:
                greeks = CryptoGreeksEngine.greeks(flag, S, K, T, r, sigma)
                diff = greeks.price - market_price

                if abs(diff) < tolerance:
                    return float(sigma)

                vega_raw = greeks.vega * 100.0
                if vega_raw < 1e-8:
                    break

                sigma = sigma - diff / vega_raw
                if sigma <= 0.001 or sigma > 20.0:
                    break
            except Exception:
                break

        # 2. Brent fallback
        def objective(sig: float) -> float:
            return CryptoGreeksEngine.price(flag, S, K, T, r, sig) - market_price

        try:
            low_sig, high_sig = 0.0001, 20.0
            if objective(low_sig) * objective(high_sig) <= 0:
                return float(brentq(objective, low_sig, high_sig, xtol=tolerance, maxiter=200))
        except Exception:
            pass

        raise ValueError(f"Implied volatility did not converge: S={S}, K={K}, T={T}, price={market_price}")
