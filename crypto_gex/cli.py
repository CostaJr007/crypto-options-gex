"""Command-line interface for Crypto Options GEX & Volatility Suite."""

from __future__ import annotations

import argparse
import uvicorn
from .models.greeks import CryptoGreeksEngine
from .models.gex import CryptoGammaExposureEngine
from .models.volatility_surface import VolatilitySurfaceEngine
from .connectors.market_data import CryptoMarketData


def main():
    parser = argparse.ArgumentParser(
        prog="crypto-gex",
        description="Crypto Options GEX & Volatility Suite CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: gex
    p_gex = subparsers.add_parser("gex", help="Calculate Net Gamma Exposure, Call/Put Walls, and Zero Gamma")
    p_gex.add_argument("--asset", default="BTC", choices=["BTC", "ETH"])
    p_gex.add_argument("--spot", type=float, default=None, help="Spot price override (defaults to Binance live)")
    p_gex.add_argument("--strikes", type=int, default=21, help="Number of strikes to evaluate")

    # Subcommand: greeks
    p_greeks = subparsers.add_parser("greeks", help="Compute Black-Scholes Greeks for crypto contract")
    p_greeks.add_argument("--flag", choices=["call", "put"], default="call")
    p_greeks.add_argument("--spot", type=float, required=True, help="Underlying spot price (e.g. 65000)")
    p_greeks.add_argument("--strike", type=float, required=True, help="Strike price (e.g. 68000)")
    p_greeks.add_argument("--days", type=float, default=14.0, help="Days to expiry")
    p_greeks.add_argument("--vol", type=float, default=0.55, help="Annualized volatility (e.g. 0.55 for 55%)")

    # Subcommand: smile
    p_smile = subparsers.add_parser("smile", help="Analyze crypto volatility skew and 25-delta risk reversal")
    p_smile.add_argument("--spot", type=float, default=65000.0)

    # Subcommand: serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", type=str, default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8002)

    args = parser.parse_args()

    if args.command == "gex":
        spot = args.spot or CryptoMarketData.get_binance_spot(f"{args.asset}USDT")
        chain = CryptoMarketData.generate_crypto_option_chain(spot=spot, strikes_count=args.strikes)
        report = CryptoGammaExposureEngine.calculate(spot=spot, df_chain=chain, asset=args.asset)

        print("=" * 60)
        print(f"CRYPTO GAMMA EXPOSURE (GEX) REPORT &mdash; {report.asset}")
        print("=" * 60)
        print(f"Spot Price:         ${report.spot_price:,.2f}")
        print(f"Total Net GEX:      ${report.total_net_gex:,.2f} / 1% move")
        print(f"Total Call GEX:     ${report.total_call_gex:,.2f}")
        print(f"Total Put GEX:      ${report.total_put_gex:,.2f}")
        print(f"Call Wall (Resist): ${report.call_wall:,.2f}")
        print(f"Put Wall (Support): ${report.put_wall:,.2f}")
        if report.zero_gamma_level:
            print(f"Zero Gamma Flip:    ${report.zero_gamma_level:,.2f}")
        print(f"Market Regime:      {report.regime}")
        print("=" * 60)

    elif args.command == "greeks":
        T = args.days / 365.0
        res = CryptoGreeksEngine.greeks(args.flag, args.spot, args.strike, T, 0.04, args.vol)
        print("=" * 60)
        print(f"CRYPTO OPTION GREEKS ({args.flag.upper()}) &mdash; 24/7 CONTINUOUS BASIS")
        print("=" * 60)
        print(f"Spot:               ${args.spot:,.2f}")
        print(f"Strike:             ${args.strike:,.2f}")
        print(f"Days to Expiry:     {args.days:.1f} days (T={T:.4f})")
        print(f"Price:              ${res.price:,.2f}")
        print(f"Delta:              {res.delta:+.4f}")
        print(f"Gamma:              {res.gamma:.8f}")
        print(f"Vega (1% vol move): ${res.vega:,.2f}")
        print(f"Theta (per day):    ${res.theta_daily:,.2f}")
        print("=" * 60)

    elif args.command == "smile":
        chain = CryptoMarketData.generate_crypto_option_chain(spot=args.spot)
        sk = VolatilitySurfaceEngine.compute_skew_metrics(chain, spot=args.spot)
        print("=" * 60)
        print(f"CRYPTO VOLATILITY SKEW & SMILE &mdash; SPOT ${args.spot:,.2f}")
        print("=" * 60)
        print(f"ATM Implied Volatility:     {sk.atm_volatility*100:.2f}%")
        print(f"25-Delta Put Skew:          {sk.put_skew_25d*100:+.2f}%")
        print(f"25-Delta Call Skew:         {sk.call_skew_25d*100:+.2f}%")
        print(f"25-Delta Risk Reversal:     {sk.risk_reversal_25d*100:+.2f}%")
        print(f"Smile Curvature/Convexity:  {sk.smile_curvature*100:+.2f}%")
        print("=" * 60)

    elif args.command == "serve":
        print(f"Starting Crypto GEX API at http://{args.host}:{args.port}")
        uvicorn.run("crypto_gex.api.server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
