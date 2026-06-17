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
The bot implements two distinct trading strategies that run in parallel:

### 1. Smart Money Concepts (SMC) Strategy
- Detects Liquidity Sweeps, BOS/CHoCH, and Order Blocks (OB) or Fair Value Gaps (FVG).
- Places **Limit Orders** at the 50% level of the detected OB/FVG.
- Requires rejection confirmation on lower timeframes.

### 2. Institutional Footprint Strategy (New)
This strategy tracks institutional activity by monitoring three specific "footprints":

- **Pillar 1: Order Absorption**
  - Detects high-volume, small-range candles where institutions are accumulating or distributing.
  - *Detection:* 1-minute bar volume > 2x average, body size < 30% of total range.
- **Pillar 2: Liquidity Sweep**
  - Identifies when price triggers stop-losses above/below recent ranges before reversing.
  - *Detection:* 10-bar high/low breakout followed by a close back inside the range.
- **Pillar 3: CVD Divergence (Cumulative Volume Delta)**
  - Measures net buying/selling pressure vs price action using tick-by-tick data over 5 minutes.
  - *Detection:* Divergence between cumulative volume delta and price trend.

**The Golden Rule (2 out of 3):**
A trade is only executed if at least 2 of the 3 pillars agree on the direction. This strategy uses **Market Orders** for immediate execution upon signal confirmation.

### Risk Management (Unified)
- **Account Risk:** Fixed at 1% of total account balance per trade.
- **Stop-Loss:** Placed just beyond the sweep levels or OB boundaries.
- **Take-Profit:** Set at a fixed 2:1 reward-to-risk ratio.

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
