import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from src.logger import get_logger

logger = get_logger('data')

TF_MAP = {
    'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30, 'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1
}

def connect():
    # Assumes MT5 terminal is running and user has logged in manually or via credentials in executor.
    if not mt5.initialize():
        logger.error('MT5 initialize failed')
        raise RuntimeError('MT5 initialize failed')

def shutdown():
    mt5.shutdown()

def get_candles(symbol, timeframe='M5', count=500):
    tf = TF_MAP.get(timeframe, mt5.TIMEFRAME_M5)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None:
        logger.error(f'No rates for {symbol} {timeframe}')
        return None
    df = pd.DataFrame(rates)
    # convert time to datetime
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df[['time','open','high','low','close','tick_volume']]
    df.columns = ['time','open','high','low','close','volume']
    return df

def get_ticks(symbol, count=1000):
    ticks = mt5.copy_ticks_from_pos(symbol, 0, count, mt5.COPY_TICKS_ALL)
    if ticks is None:
        logger.error(f'No ticks for {symbol}')
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def get_last_5m_ticks(symbol):
    to_date = datetime.now()
    from_date = to_date - timedelta(minutes=5)
    ticks = mt5.copy_ticks_range(symbol, from_date, to_date, mt5.COPY_TICKS_ALL)
    if ticks is None:
        logger.error(f'No ticks for {symbol} in last 5m')
        return None
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df
