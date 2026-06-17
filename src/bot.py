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
        tf_htf, tf_setup, tf_entry = CONFIG['TIMEFRAMES']
        df_htf = data.get_candles(symbol, timeframe=tf_htf, count=300)
        df_setup = data.get_candles(symbol, timeframe=tf_setup, count=300)
        df_entry = data.get_candles(symbol, timeframe=tf_entry, count=200)
        if df_htf is None or df_setup is None or df_entry is None:
            logger.warning('Missing data for %s - skipping', symbol)
            continue
        if not signals.session_filter():
            logger.info('Outside session window - skipping')
            continue
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
                continue
            entry_price = signals.entry_zone_50(chosen_zone)
            if entry_price is None:
                logger.info('No entry price derived - skipping')
                continue
            # check rejection on entry timeframe
            rej = signals.rejection_check(df_entry, entry_price)
            if not rej:
                logger.info('No rejection at entry timeframe - skipping')
                continue
            # Compute SL/TP: SL beyond liquidity or OB - for demo simple SL (use fixed pip cushion)
            # NOTE: for production compute SL precise to the OB/liquidity area
            sl = entry_price - 0.002 if entry_price>df_entry['close'].iloc[-1] else entry_price + 0.002
            tp = entry_price + (abs(entry_price - sl) * 2.0)  # 1:2 by default
            lot = risk.compute_lot_from_risk(mt5, symbol, balance, CONFIG['RISK_PERCENT'], abs(entry_price-sl))
            lot = max(CONFIG['DEFAULT_LOT_MIN'], min(lot, CONFIG['DEFAULT_LOT_MAX']))
            logger.info('Placing limit order for %s at %s lot=%s sl=%s tp=%s', symbol, entry_price, lot, sl, tp)
            res = executor.place_limit_order(symbol, lot, entry_price, sl, tp, magic=CONFIG['MAGIC'])
            logger.info('Order send result: %s', res)
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
