# SMC Trader - Automated Smart Money Concepts (SMC) Bot for MT5 (Forex / XAU / BTC)

**Warning & Disclaimer:** This project is an educational starter implementation. Trading involves risk. **Test thoroughly on demo accounts** before running with real money. The author is not responsible for any loss.

## What this project contains
- `src/` - core Python modules (config, data, indicators, signals, risk, executor, bot, logger)
- `.env.example` - environment variables template
- `requirements.txt` - Python packages to install
- `run.sh` - helper script to run the bot

## Quick Setup (local machine)
1. Install MetaTrader5 terminal and login to your broker account (Exness MT5 recommended). Keep MT5 running on same machine.
2. Clone or unzip this project and `cd` into the project folder.
3. Create a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / macOS
   venv\Scripts\activate    # Windows
   ```
4. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` and fill your secrets (MT5 account, password, server, symbols, risk% etc.).
6. Start MT5 terminal and make sure the account server string in `.env` matches the MT5 login dialog.
7. Run the bot (one-shot check or loop):
   ```bash
   python src/bot.py
   ```

## Files & How to change behavior
- `src/config.py` loads `.env` values. Change defaults there or edit `.env`.
- `src/signals.py` contains the strategy implementation (Liquidity sweep → BOS → OB/FVG → 50% Entry → rejection check).
  - Tweak timeframes, thresholds, and the `MIN_CONFIRM` constants to change sensitivity.
- `src/risk.py` controls position sizing. It uses MT5 symbol info to compute approximate lot; you can change `RISK_PERCENT` in `.env`.

## How it works (high-level)
1. Load multi-timeframe OHLC from MT5 for configured symbols.
2. Use `smartmoneyconcepts` indicators (swing, bos/choch, fvg, ob) to detect SMC conditions.
3. If filters pass (session filter, no-news placeholder), signal is validated and a limit order is placed at 50% of OB/FVG with SL & TP calculated.
4. Risk manager determines lot size for target 1% (or configured) risk per trade.

## Limitations & TODO
- News filter is a placeholder (not implemented). Consider integrating a news API or a calendar to skip high-impact events.
- Strategy logic requires heavy backtesting — this repo provides a runtime detector, not a full-fledged robust production system.
- Smart Money Concepts indicators (SMC) rely on clean OHLC. Use high-quality broker data for reliability.

## Run modes
- One-shot: run `python src/bot.py` to check signals and place orders once.
- Continuous: use a scheduler (systemd, cron, or process manager) or wrap `bot.run_loop()` to run periodically (e.g., every 5 minutes).

## Safety checklist before going live
- Test on demo account for minimum 100+ trades to evaluate edge cases.
- Validate risk manager output for each symbol & stop loss.
- Monitor logs: `logs/bot.log` and trades in MT5 Terminal.

---
Happy building — update README if you customize entries!
