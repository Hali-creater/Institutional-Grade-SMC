# Institutional Footprint Trader - Automated Scalping Bot for MT5

**Warning & Disclaimer:** This project is an educational starter implementation. Trading involves risk. **Test thoroughly on demo accounts** before running with real money. The author is not responsible for any loss.

## The Strategy
The bot implements an Institutional Footprint Strategy that tracks institutional activity by monitoring three specific footprints:

### Pillar 1: Order Absorption
- Detects high-volume, small-range candles where institutions are accumulating or distributing.
- *Detection:* 1-minute bar volume > 2x average, body size < 30% of total range.

### Pillar 2: Liquidity Sweep
- Identifies when price triggers stop-losses above/below recent ranges before reversing.
- *Detection:* 10-bar high/low breakout followed by a close back inside the range.

### Pillar 3: CVD Divergence (Cumulative Volume Delta)
- Measures net buying/selling pressure vs price action using tick-by-tick data over 5 minutes.
- *Detection:* Divergence between cumulative volume delta and price trend.

### The Golden Rule (2 out of 3)
A trade is only executed if at least 2 of the 3 pillars agree on the direction. This strategy uses **Market Orders** for immediate execution upon signal confirmation.

## Risk Management
- **Account Risk:** Fixed at 1% of total account balance per trade.
- **Stop-Loss:** Placed just beyond the sweep levels.
- **Take-Profit:** Set at a fixed 2:1 reward-to-risk ratio.

## Project Structure
- `src/` - core Python modules (config, data, indicators, signals, risk, executor, bot, logger)
- `.env.example` - environment variables template
- `requirements.txt` - Python packages to install
- `run.sh` - helper script to run the bot

## Quick Setup
1. Install MetaTrader5 terminal and login to your broker account.
2. Clone this project and `cd` into the project folder.
3. Install Python packages: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill your secrets.
5. Run the bot: `python src/bot.py`.

## Files & How to change behavior
- `src/config.py` loads `.env` values.
- `src/signals.py` contains the signal confluence logic (Golden Rule).
- `src/indicators.py` contains the implementation of the 3 pillars.
- `src/risk.py` controls position sizing (1% risk rule).

---
Happy building!
