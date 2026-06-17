from src.indicators import (
    find_swings, find_fvgs, find_obs, find_bos_choch,
    check_order_absorption, check_liquidity_sweep, calculate_cvd
)
from src.logger import get_logger
from datetime import datetime, time as dtime
from src import data
import pandas as pd

logger = get_logger('signals')

def session_filter(now=None):
    # London session: 12:30 - 16:30 IST (UTC+5:30). This function expects local system time in IST.
    # For simplicity we check hour ranges (24h) - user machine should be IST or convert accordingly.
    if now is None:
        now = datetime.now()
    hour = now.hour
    minute = now.minute
    # London roughly 12:30-16:30 IST
    if (hour==12 and minute>=30) or (12 < hour < 16) or (hour==16 and minute<=30):
        return True
    # NY session 19:00-23:30 IST
    if (hour==19 and minute>=0) or (19 < hour < 23) or (hour==23 and minute<=30):
        return True
    return False

def liquidity_sweep_check(df_htf):
    # Simple heuristic: look if a recent candle makes a new high/low beyond previous swing
    swings = find_swings(df_htf, swing_length=50)
    if swings is None or swings.empty:
        return False
    last = df_htf.iloc[-1]
    # try to use swings structure; structure of swings depends on package output
    if 'high' in swings.columns:
        prev_high = swings['high'].max()
        return last['high'] > prev_high
    return False

def bos_check(df_setup):
    swings = find_swings(df_setup, swing_length=30)
    b = find_bos_choch(df_setup, swings)
    return b

def find_ob_fvg(df_setup):
    swings = find_swings(df_setup, swing_length=30)
    obs = find_obs(df_setup, swings)
    fvgs = find_fvgs(df_setup)
    return obs, fvgs

def entry_zone_50(ob_zone):
    if ob_zone is None:
        return None
    try:
        # ob_zone may be dict-like or DataFrame row; handle both
        if hasattr(ob_zone, 'get'):
            hi = float(ob_zone.get('high', ob_zone.get('high_price', None)))
            lo = float(ob_zone.get('low', ob_zone.get('low_price', None)))
        else:
            hi = float(ob_zone['high'])
            lo = float(ob_zone['low'])
        return (hi + lo) / 2.0
    except Exception as e:
        logger.error('entry_zone_50 error: %s', e)
        return None

def rejection_check(df_entry, entry_price):
    # Look for a rejection candle at the entry timeframe: last candle wick against entry side
    last = df_entry.iloc[-1]
    # For a buy entry, we want a bullish rejection (close > open and low wick near entry)
    try:
        if last['close'] > last['open'] and last['low'] <= entry_price:
            return True
        if last['close'] < last['open'] and last['high'] >= entry_price:
            return True
    except Exception as e:
        logger.error('rejection check error: %s', e)
    return False

def check_cvd_divergence(symbol, df_m1):
    """
    Pillar 3: CVD Divergence
    - Buy: CVD rising, Price flat/falling
    - Sell: CVD falling, Price flat/rising
    """
    ticks_5m = data.get_last_5m_ticks(symbol)
    if ticks_5m is None or ticks_5m.empty:
        return 0

    cvd_values = calculate_cvd(ticks_5m)
    if not cvd_values:
        return 0

    # Simple divergence check over 5 min period
    # Compare start and end of 5 min period
    cvd_start = cvd_values[0]
    cvd_end = cvd_values[-1]
    cvd_trend = 1 if cvd_end > cvd_start else -1 if cvd_end < cvd_start else 0

    # Price trend over last 5 M1 bars
    if len(df_m1) < 5:
        return 0

    price_start = df_m1['close'].iloc[-5]
    price_end = df_m1['close'].iloc[-1]
    price_trend = 1 if price_end > price_start else -1 if price_end < price_start else 0

    # BUY divergence: CVD rising (1), Price flat (0) or falling (-1)
    if cvd_trend == 1 and price_trend <= 0:
        return 1

    # SELL divergence: CVD falling (-1), Price flat (0) or rising (1)
    if cvd_trend == -1 and price_trend >= 0:
        return -1

    return 0

def get_strategy_signals(symbol):
    """
    The Golden Rule: 2 out of 3
    """
    # M1 for Absorption and Price Trend
    df_m1 = data.get_candles(symbol, timeframe='M1', count=50)
    if df_m1 is None or df_m1.empty:
        return "NEUTRAL", 0

    p1 = check_order_absorption(df_m1)
    p2 = check_liquidity_sweep(df_m1)
    p3 = check_cvd_divergence(symbol, df_m1)

    logger.info(f"Signals for {symbol}: Absorption={p1}, Sweep={p2}, CVD={p3}")

    buy_score = (1 if p1 == 1 else 0) + (1 if p2 == 1 else 0) + (1 if p3 == 1 else 0)
    sell_score = (1 if p1 == -1 else 0) + (1 if p2 == -1 else 0) + (1 if p3 == -1 else 0)

    if buy_score >= 2:
        return "BUY", buy_score
    if sell_score >= 2:
        return "SELL", sell_score

    return "NEUTRAL", 0
