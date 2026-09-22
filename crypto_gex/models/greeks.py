"""Vectorized Black-Scholes-Merton Pricing and Greeks for 24/7 Crypto Options."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Union
import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class OptionGreeks:
    price: float
    delta: float
    gamma: float
    vega: float
    theta_daily: float
    rho: float


class CryptoGreeksEngine:
    """Analytical Black-Scholes engine for 24/7 Continuous Crypto Derivatives (Deribit/Binance)."""

    @staticmethod
    def _d1_d2(
        S: Union[float, np.ndarray],
        K: Union[float, np.ndarray],
        T: Union[float, np.ndarray],
        r: Union[float, np.ndarray],
        sigma: Union[float, np.ndarray],
        q: Union[float, np.ndarray] = 0.0,
    ) -> tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        if np.any(T <= 0) or np.any(sigma <= 0):
            raise ValueError("Time to maturity (T) and volatility (sigma) must be strictly positive.")
        if np.any(S <= 0) or np.any(K <= 0):
            raise ValueError("Spot price (S) and strike price (K) must be strictly positive.")

        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        return d1, d2

    @classmethod
    def price(
        cls,
        flag: Literal["call", "put"],
        S: Union[float, np.ndarray],
        K: Union[float, np.ndarray],
        T: Union[float, np.ndarray],
        r: Union[float, np.ndarray],
        sigma: Union[float, np.ndarray],
        q: Union[float, np.ndarray] = 0.0,
    ) -> Union[float, np.ndarray]:
        d1, d2 = cls._d1_d2(S, K, T, r, sigma, q)
        discount_r = np.exp(-r * T)
        discount_q = np.exp(-q * T)

        is_call = (flag.lower() == "call")
        if is_call:
            return S * discount_q * norm.cdf(d1) - K * discount_r * norm.cdf(d2)
        else:
            return K * discount_r * norm.cdf(-d2) - S * discount_q * norm.cdf(-d1)

    @classmethod
    def greeks(
        cls,
        flag: Literal["call", "put"],
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0.0,
    ) -> OptionGreeks:
        d1, d2 = cls._d1_d2(S, K, T, r, sigma, q)
        sqrt_T = math.sqrt(T)
        pdf_d1 = norm.pdf(d1)
        discount_r = math.exp(-r * T)
        discount_q = math.exp(-q * T)

        is_call = (flag.lower() == "call")
        theta_basis = 365.0  # Continuous 24/7 crypto calendar

        if is_call:
            price = S * discount_q * norm.cdf(d1) - K * discount_r * norm.cdf(d2)
            delta = discount_q * norm.cdf(d1)
            rho = 0.01 * K * T * discount_r * norm.cdf(d2)
            theta = (
                -(S * discount_q * pdf_d1 * sigma) / (2 * sqrt_T)
                - r * K * discount_r * norm.cdf(d2)
                + q * S * discount_q * norm.cdf(d1)
            ) / theta_basis
        else:
            price = K * discount_r * norm.cdf(-d2) - S * discount_q * norm.cdf(-d1)
            delta = -discount_q * norm.cdf(-d1)
            rho = -0.01 * K * T * discount_r * norm.cdf(-d2)
            theta = (
                -(S * discount_q * pdf_d1 * sigma) / (2 * sqrt_T)
                + r * K * discount_r * norm.cdf(-d2)
                - q * S * discount_q * norm.cdf(-d1)
            ) / theta_basis

        gamma = (discount_q * pdf_d1) / (S * sigma * sqrt_T)
        vega = 0.01 * S * discount_q * sqrt_T * pdf_d1

        return OptionGreeks(
            price=float(price),
            delta=float(delta),
            gamma=float(gamma),
            vega=float(vega),
            theta_daily=float(theta),
            rho=float(rho),
        )
