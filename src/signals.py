from src.indicators import find_swings, find_fvgs, find_obs, find_bos_choch
from src.logger import get_logger
from datetime import datetime, time as dtime

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
