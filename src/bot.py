import time
import MetaTrader5 as mt5
from src.config import CONFIG
from src.logger import get_logger
from src import data, indicators, signals, risk, executor
import pandas as pd

logger = get_logger('bot')

def check_smc_strategy(symbol, balance):
    tf_htf, tf_setup, tf_entry = CONFIG['TIMEFRAMES']
    df_htf = data.get_candles(symbol, timeframe=tf_htf, count=300)
    df_setup = data.get_candles(symbol, timeframe=tf_setup, count=300)
    df_entry = data.get_candles(symbol, timeframe=tf_entry, count=200)

    if df_htf is None or df_setup is None or df_entry is None:
        logger.warning('Missing data for SMC strategy on %s - skipping', symbol)
        return

    if not signals.session_filter():
        logger.info('Outside session window for SMC strategy - skipping')
        return

    try:
        liquidity = signals.liquidity_sweep_check(df_htf)
        bos = signals.bos_check(df_setup)
        obs, fvgs = signals.find_ob_fvg(df_setup)
        chosen_zone = None
        # pick the freshest OB or FVG (this is a simple pick)
        if obs is not None and len(obs)>0:
            chosen_zone = obs[-1]
        elif fvgs is not None and len(fvgs)>0:
            chosen_zone = fvgs[-1]

        if chosen_zone is None:
            logger.info('No OB/FVG found for %s', symbol)
            return

        entry_price = signals.entry_zone_50(chosen_zone)
        if entry_price is None:
            logger.info('No entry price derived - skipping')
            return

        # check rejection on entry timeframe
        rej = signals.rejection_check(df_entry, entry_price)
        if not rej:
            logger.info('No rejection at entry timeframe - skipping')
            return

        # Compute SL/TP: SL beyond liquidity or OB - for demo simple SL (use fixed pip cushion)
        sl = entry_price - 0.002 if entry_price>df_entry['close'].iloc[-1] else entry_price + 0.002
        tp = entry_price + (abs(entry_price - sl) * 2.0)  # 1:2 by default

        lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], abs(entry_price-sl))
        lot = max(CONFIG['DEFAULT_LOT_MIN'], min(lot, CONFIG['DEFAULT_LOT_MAX']))

        logger.info('Placing SMC limit order for %s at %s lot=%s sl=%s tp=%s', symbol, entry_price, lot, sl, tp)
        res = executor.place_limit_order(symbol, lot, entry_price, sl, tp, magic=CONFIG['MAGIC'])
        logger.info('SMC Order send result: %s', res)
    except Exception as e:
        logger.exception('Error checking SMC strategy for %s: %s', symbol, e)

def check_institutional_strategy(symbol, balance):
    direction, score = signals.get_strategy_signals(symbol)

    if direction == "NEUTRAL":
        logger.info(f"No strong Institutional signal for {symbol} (score: {score})")
        return

    logger.info(f"Institutional Signal detected for {symbol}: {direction} (score: {score})")

    try:
        df_m1 = data.get_candles(symbol, timeframe='M1', count=20)
        if df_m1 is None or df_m1.empty:
            return

        last_bar = df_m1.iloc[-1]
        entry_price = last_bar['close']

        lookback_10 = df_m1.iloc[-11:-1]
        hh = lookback_10['high'].max()
        ll = lookback_10['low'].min()

        if direction == "BUY":
            # Stop-loss just below the low that was swept (or the 10-bar low)
            sl = min(ll, last_bar['low']) - 0.0001
            risk_dist = entry_price - sl
            tp = entry_price + (2 * risk_dist)

            lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], risk_dist)
            lot = max(CONFIG['DEFAULT_LOT_MIN'], min(lot, CONFIG['DEFAULT_LOT_MAX']))
            logger.info(f"Placing Institutional BUY market order for {symbol} at {entry_price}, sl={sl}, tp={tp}, lot={lot}")
            executor.place_market_order(symbol, lot, "buy", sl, tp, magic=CONFIG['MAGIC'])

        elif direction == "SELL":
            # Stop-loss just above the high that was swept (or the 10-bar high)
            sl = max(hh, last_bar['high']) + 0.0001
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

        # Run original SMC Strategy
        check_smc_strategy(symbol, balance)

        # Run new Institutional Strategy
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
