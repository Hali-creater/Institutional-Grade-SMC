import time
import MetaTrader5 as mt5
from src.config import CONFIG
from src.logger import get_logger
from src import data, indicators, signals, risk, executor
import pandas as pd

logger = get_logger('bot')

def run_once():
    data.connect()
    # Account info (requires MT5 logged in)
    account_info = mt5.account_info()
    balance = account_info.balance if account_info else 0
    logger.info('Account balance: %s', balance)
    for symbol in CONFIG['SYMBOLS']:
        logger.info('Checking symbol: %s', symbol)

        # We focus on the new strategy logic
        direction, score = signals.get_strategy_signals(symbol)

        if direction == "NEUTRAL":
            logger.info(f"No strong signal for {symbol} (score: {score})")
            continue

        logger.info(f"Signal detected for {symbol}: {direction} (score: {score})")

        try:
            # For Pillar 2: Stop-loss goes just beyond the sweep level (the high or low that was broken)
            # We fetch M1 data to find the recent high/low
            df_m1 = data.get_candles(symbol, timeframe='M1', count=20)
            if df_m1 is None or df_m1.empty:
                continue

            last_bar = df_m1.iloc[-1]
            entry_price = last_bar['close']

            lookback_10 = df_m1.iloc[-11:-1]
            hh = lookback_10['high'].max()
            ll = lookback_10['low'].min()

            if direction == "BUY":
                # Stop-loss just below the low that was swept (or the 10-bar low)
                sl = min(ll, last_bar['low']) - 0.0001 # small buffer
                risk_dist = entry_price - sl
                tp = entry_price + (2 * risk_dist)

                lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], risk_dist)
                logger.info(f"Placing BUY market order for {symbol} at {entry_price}, sl={sl}, tp={tp}, lot={lot}")
                executor.place_market_order(symbol, lot, "buy", sl, tp, magic=CONFIG['MAGIC'])

            elif direction == "SELL":
                # Stop-loss just above the high that was swept (or the 10-bar high)
                sl = max(hh, last_bar['high']) + 0.0001 # small buffer
                risk_dist = sl - entry_price
                tp = entry_price - (2 * risk_dist)

                lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], risk_dist)
                logger.info(f"Placing SELL market order for {symbol} at {entry_price}, sl={sl}, tp={tp}, lot={lot}")
                executor.place_market_order(symbol, lot, "sell", sl, tp, magic=CONFIG['MAGIC'])

        except Exception as e:
            logger.exception('Error checking symbol %s: %s', symbol, e)
    data.shutdown()

def run_loop():
    interval = CONFIG['RUN_LOOP_INTERVAL_SECONDS']
    logger.info('Starting run loop. Interval=%s seconds', interval)
    while True:
        run_once()
        time.sleep(interval)

if __name__ == '__main__':
    run_once()
