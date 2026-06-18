import time
import MetaTrader5 as mt5
from src.config import CONFIG
from src.logger import get_logger
from src import data, indicators, signals, risk, executor
import pandas as pd

logger = get_logger('bot')

def check_institutional_strategy(symbol, balance):
    # Check for high-impact news events first
    if signals.check_news_events(symbol):
        logger.info(f"Skipping {symbol} due to high-impact news event.")
        return

    direction, score = signals.get_strategy_signals(symbol)

    if direction == "NEUTRAL":
        logger.info(f"No strong Institutional signal for {symbol} (score: {score})")
        return

    logger.info(f"Institutional Signal detected for {symbol}: {direction} (score: {score})")

    try:
        # Get symbol info for point value
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Failed to get symbol info for {symbol}")
            return

        point = symbol_info.point
        buffer = CONFIG['STOP_DISTANCE_PIPS'] * point

        df_m1 = data.get_candles(symbol, timeframe='M1', count=20)
        if df_m1 is None or df_m1.empty:
            return

        last_bar = df_m1.iloc[-1]
        entry_price = last_bar['close']

        lookback_10 = df_m1.iloc[-11:-1]
        hh = lookback_10['high'].max()
        ll = lookback_10['low'].min()

        if direction == "BUY":
            # Stop-loss just below the low that was swept (or the 10-bar low) + buffer
            sl = min(ll, last_bar['low']) - buffer
            risk_dist = entry_price - sl
            tp = entry_price + (2 * risk_dist)

            lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], risk_dist)
            lot = max(CONFIG['DEFAULT_LOT_MIN'], min(lot, CONFIG['DEFAULT_LOT_MAX']))
            logger.info(f"Placing Institutional BUY market order for {symbol} at {entry_price}, sl={sl}, tp={tp}, lot={lot}")
            executor.place_market_order(symbol, lot, "buy", sl, tp, magic=CONFIG['MAGIC'])

        elif direction == "SELL":
            # Stop-loss just above the high that was swept (or the 10-bar high) + buffer
            sl = max(hh, last_bar['high']) + buffer
            risk_dist = sl - entry_price
            tp = entry_price - (2 * risk_dist)

            lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], risk_dist)
            lot = max(CONFIG['DEFAULT_LOT_MIN'], min(lot, CONFIG['DEFAULT_LOT_MAX']))
            logger.info(f"Placing Institutional SELL market order for {symbol} at {entry_price}, sl={sl}, tp={tp}, lot={lot}")
            executor.place_market_order(symbol, lot, "sell", sl, tp, magic=CONFIG['MAGIC'])

    except Exception as e:
        logger.exception('Error checking Institutional strategy for %s: %s', symbol, e)

def run_once():
    data.connect()
    account_info = mt5.account_info()
    balance = account_info.balance if account_info else 0
    logger.info('Account balance: %s', balance)

    for symbol in CONFIG['SYMBOLS']:
        logger.info('Checking symbol: %s', symbol)

        # Run Institutional Strategy
        check_institutional_strategy(symbol, balance)

    data.shutdown()

def run_loop():
    interval = CONFIG['RUN_LOOP_INTERVAL_SECONDS']
    logger.info('Starting run loop. Interval=%s seconds', interval)
    while True:
        run_once()
        time.sleep(interval)

if __name__ == '__main__':
    run_once()
