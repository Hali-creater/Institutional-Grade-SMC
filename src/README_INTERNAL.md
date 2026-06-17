Internal notes for src modules:
- `data.py` : relies on MT5 Python package to fetch candles. Ensure MT5 terminal is running.
- `indicators.py` : thin wrappers around smartmoneyconcepts functions. Adjust parameters as needed.
- `signals.py` : core SMC logical checks; the heuristics are intentionally simple. Improve with more robust sequence checks.
- `risk.py` : rough lot calculation. For production, replace with exact pip/tick formulas using broker instrument metadata.
- `executor.py` : uses MT5 order_send. Test on demo before using live accounts.
