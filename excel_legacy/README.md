# Legacy Workbook Provenance

The original macro-enabled workbook (`PLANILHA OBT CRIPTO.xlsm`) was
**reverse-engineered and then removed from version control**. Binaries with VBA
macros are intentionally not shipped: they bloat clones, trigger security warnings,
and redistribute third-party material. The audited logic lives on as extracted text
in `vba_legacy/` and as the Python engine in `crypto_gex/`.

| Item | Detail |
|---|---|
| Original file | `PLANILHA OBT CRIPTO.xlsm` (~2 MB) |
| Sanitized copy (removed) | `excel_legacy/crypto_options_gex_legacy.xlsm` |
| Sheets | `CALL`/`PUT` (GEX columns), `CALLVOL`/`PUTVOL`, `VOLH`, `VOLSPUT`, `RSP`, `VOL`, `GAMMA`, `TELA`, `GBM`, `Base de Dados GBM` |
| VBA | `OptionGreeks_BlackScholes.bas`, `ExportarGrafico_RR.bas`, `ProgressBar_Win32API.frm`, `Servidor1_RTD_Selector.frm` |

## What the workbook got wrong (fixed in Python)

- `CALL!J` / `PUT!J` computed `Γ × OI × 100` — that is **not** GEX. Correct (SqueezeMetrics convention, as in `gex.py`): `call_gex = +OI·Γ·S²·0.01·mult`, `put_gex = −OI·Γ·S²·0.01·mult` (off by ~4 orders of magnitude for BTC-scale spot).
- Legacy Greeks VBA omitted the `e^(−qT)` dividend-discount factors and the dividend carry terms in Theta (fixed version archived in `vba_legacy/`).
- Python additionally implements true 25-delta skew via Black-Scholes inversion (not fixed ±8% strike proxies) and cumulative zero-gamma flip detection.

## Runtime note

The engine builds chains from user-supplied data or live Binance spot with synthetic
fallback (`connectors/market_data.py`); no legacy binary is required to run or test
this repo.
