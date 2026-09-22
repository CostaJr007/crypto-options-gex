# Crypto Options Analytics & Gamma Exposure (GEX) Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-7%20passed-brightgreen.svg)]()
[![Market: Crypto](https://img.shields.io/badge/market-BTC%20%7C%20ETH%20%7C%20Deribit-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Quantitative Crypto Options Analytics, Market Maker Gamma Exposure (GEX), and Volatility Surface Engine for BTC & ETH.**

This repository modernizes legacy crypto options workbooks (see `excel_legacy/README.md` for provenance) into a research-grade Python engine for digital asset derivatives:
- **Net Dealer Gamma Exposure (GEX)**: Track where market makers must hedge spot to remain delta-neutral.
- **Key Market Levels**: Automatic detection of the **Call Wall** (Major Resistance), **Put Wall** (Major Support), and **Zero Gamma Flip Level** (Regime shift).
- **24/7 Continuous Pricing**: Black-Scholes-Merton engine adapted for nonstop cryptocurrency trading (365 calendar days).
- **Implied Volatility Smile & 25-Delta Risk Reversal Skew**: Real-time evaluation of market sentiment, crash risk, and tail-risk pricing.
- **FastAPI REST Microservice & CLI Tooling**: Cloud-native deployment ready for trading desks and automated execution bots.

---

## 📐 Quantitative Models

### 1. Market Maker Gamma Exposure (GEX)
Option market makers continuously delta-hedge their portfolios. The aggregate Gamma Exposure per 1% spot move is defined as:

$$\text{Call GEX}_i = \text{OI}_{\text{call}, i} \cdot \Gamma_i \cdot S^2 \cdot 0.01$$

$$\text{Put GEX}_i = -\text{OI}_{\text{put}, i} \cdot \Gamma_i \cdot S^2 \cdot 0.01$$

$$\text{Net GEX} = \sum_i \left( \text{Call GEX}_i + \text{Put GEX}_i \right)$$

* **Long Gamma Regime ($\text{Net GEX} > 0$):** Market makers buy low and sell high to rebalance delta, dampening market volatility (mean-reverting behavior).
* **Short Gamma Regime ($\text{Net GEX} < 0$):** Market makers must sell as prices drop and buy as prices rally, amplifying spot market moves (trend-acceleration / cascade risk).
* **Call Wall:** The strike with the highest positive Call Gamma (peak dealer resistance).
* **Put Wall:** The strike with the deepest negative Put Gamma (peak dealer support).
* **Zero Gamma Level:** The price level where aggregate GEX crosses zero, marking the transition between stabilizing and accelerating volatility regimes.

### 2. Analytical Greeks (Continuous 24/7 Basis)
Given the continuous operation of crypto markets, Theta and time parameters are parameterized on a 365-day continuous basis:

$$\Theta_{\text{daily}} = -\frac{S e^{-qT}\phi(d_1)\sigma}{2\sqrt{T} \times 365} - \frac{r K e^{-rT}\mathcal{N}(d_2)}{365}$$

### 3. Volatility Skew & 25-Delta Risk Reversal
Quantifies downside protection demand vs upside speculation:

$$\text{RR}_{25\Delta} = \sigma_{\text{call}, 25\Delta} - \sigma_{\text{put}, 25\Delta}$$

---

## ⚡ Quick Start

### Installation

```bash
git clone https://github.com/CostaJr007/crypto-options-gex.git
cd crypto-options-gex
pip install -e .
```

### Running Tests

```bash
pytest tests -v
```

### CLI Usage

```bash
# Calculate Gamma Exposure (GEX), Walls and Zero Gamma for Bitcoin
crypto-gex gex --asset BTC --spot 65000 --strikes 21

# Calculate analytical Greeks for a crypto option
crypto-gex greeks --flag call --spot 65000 --strike 68000 --days 14 --vol 0.55

# Analyze volatility smile and 25-delta risk reversal
crypto-gex smile --spot 65000

# Start FastAPI service
crypto-gex serve --port 8000
```

---

## 🌐 FastAPI Endpoints

- `GET /health`: Service health check.
- `POST /api/v1/gex`: Generates complete GEX report (Net GEX, Call Wall, Put Wall, Zero Gamma, Strike-by-strike breakdown).
- `POST /api/v1/greeks`: Calculates Black-Scholes price and analytical Greeks.
- `POST /api/v1/smile`: Returns ATM volatility, 25-delta put skew, call skew, and risk reversal.

Interactive API Swagger documentation is available at `http://localhost:8000/docs`.

---

## 🗄️ Legacy VBA Archive (`vba_legacy/`)
Audited source code extracted from the legacy crypto options workbook (see `excel_legacy/README.md` for provenance):
- `OptionGreeks_BlackScholes.bas`: Full analytical Greeks implementation (Peter McPhee base).
- `ProgressBar_Win32API.frm`: Borderless progress bar using 64-bit Windows API (`User32.dll`).
- `ExportarGrafico_RR.bas`: Automated Risk-Reversal chart exporter.
- `Servidor1_RTD_Selector.frm`: Platform RTD selector (Workbook Password: `12345`).

---

## 📄 License
MIT License. Author: [Adeilson da Costa (Costa Junior)](https://github.com/CostaJr007) — Ottawa, Canada.
