"""FastAPI Microservice for Crypto Options GEX & Greeks."""

from __future__ import annotations

from typing import List, Literal, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd

from ..models.greeks import CryptoGreeksEngine
from ..models.gex import CryptoGammaExposureEngine
from ..models.implied_vol import ImpliedVolatilitySolver
from ..models.volatility_surface import VolatilitySurfaceEngine
from ..connectors.market_data import CryptoMarketData


app = FastAPI(
    title="Crypto Options GEX & Volatility Suite API",
    description="Real-time Dealer Gamma Exposure (GEX), Call/Put Walls, Volatility Skew & Black-Scholes Greeks",
    version="1.0.0"
)


class CryptoGreeksRequest(BaseModel):
    flag: Literal["call", "put"]
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    time_to_maturity: float = Field(..., gt=0, description="Time to expiry in years (e.g. 14/365)")
    risk_free_rate: float = Field(0.04)
    volatility: float = Field(..., gt=0, description="Annualized volatility (e.g. 0.60 for 60%)")


class CryptoGexRequest(BaseModel):
    asset: str = Field("BTC", description="Asset symbol (BTC or ETH)")
    spot: Optional[float] = Field(None, description="Spot price override (or fetch live)")
    strikes_count: int = Field(21, ge=5, le=51)


class ImpliedVolRequest(BaseModel):
    market_price: float = Field(..., gt=0)
    flag: Literal["call", "put"]
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    time_to_maturity: float = Field(..., gt=0)
    risk_free_rate: float = Field(0.04)


@app.get("/health")
def health():
    return {"status": "ok", "service": "crypto-options-gex", "market": "Crypto / Deribit & Binance"}


@app.post("/api/v1/greeks")
def calculate_greeks(req: CryptoGreeksRequest):
    try:
        greeks = CryptoGreeksEngine.greeks(
            flag=req.flag,
            S=req.spot,
            K=req.strike,
            T=req.time_to_maturity,
            r=req.risk_free_rate,
            sigma=req.volatility
        )
        return {
            "price": greeks.price,
            "delta": greeks.delta,
            "gamma": greeks.gamma,
            "vega": greeks.vega,
            "theta_daily": greeks.theta_daily,
            "rho": greeks.rho
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/gex")
def calculate_gex(req: CryptoGexRequest):
    try:
        spot = req.spot or CryptoMarketData.get_binance_spot(f"{req.asset}USDT")
        chain = CryptoMarketData.generate_crypto_option_chain(spot=spot, strikes_count=req.strikes_count)
        report = CryptoGammaExposureEngine.calculate(spot=spot, df_chain=chain, asset=req.asset)

        return {
            "asset": report.asset,
            "spot_price": report.spot_price,
            "total_net_gex": report.total_net_gex,
            "total_call_gex": report.total_call_gex,
            "total_put_gex": report.total_put_gex,
            "call_wall": report.call_wall,
            "put_wall": report.put_wall,
            "zero_gamma_level": report.zero_gamma_level,
            "regime": report.regime,
            "strikes": [
                {
                    "strike": s.strike,
                    "net_gex": s.net_gex,
                    "call_gex": s.call_gex,
                    "put_gex": s.put_gex,
                    "call_oi": s.call_open_interest,
                    "put_oi": s.put_open_interest
                }
                for s in report.by_strike
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/smile")
def analyze_smile(spot: float = 65000.0):
    try:
        chain = CryptoMarketData.generate_crypto_option_chain(spot=spot)
        metrics = VolatilitySurfaceEngine.compute_skew_metrics(chain, spot=spot)
        return {
            "spot_price": spot,
            "atm_volatility": metrics.atm_volatility,
            "put_skew_25d": metrics.put_skew_25d,
            "call_skew_25d": metrics.call_skew_25d,
            "risk_reversal_25d": metrics.risk_reversal_25d,
            "smile_curvature": metrics.smile_curvature
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
