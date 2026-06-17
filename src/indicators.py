# Wrappers around smartmoneyconcepts. These helpers return objects you can use for checks.
from smartmoneyconcepts import fvg, ob, swing_highs_lows, bos_choch
from src.logger import get_logger
import MetaTrader5 as mt5
import pandas as pd

logger = get_logger('indicators')

def find_swings(df, swing_length=20):
    try:
        sw = swing_highs_lows(df, swing_length=swing_length)
        return sw
    except Exception as e:
        logger.error('Swing calc error: %s', e)
        return None

def find_fvgs(df, join_consecutive=False):
    try:
        f = fvg(df, join_consecutive=join_consecutive)
        return f
    except Exception as e:
        logger.error('FVG calc error: %s', e)
        return None

def find_obs(df, swings):
    try:
        o = ob(df, swings)
        return o
    except Exception as e:
        logger.error('OB calc error: %s', e)
        return None

def find_bos_choch(df, swings):
    try:
        b = bos_choch(df, swings, close_break=True)
        return b
    except Exception as e:
        logger.error('BOS/CHoCH calc error: %s', e)
        return None

def check_order_absorption(df):
    """
    Pillar 1: Order Absorption
    - Look at the most recent 1-minute bar.
    - If volume > 2x average (20-bar lookback).
    - Bar body < 30% of total range.
    """
    if len(df) < 21:
        return 0

    last_bar = df.iloc[-1]
    avg_volume = df['volume'].iloc[-21:-1].mean()

    range_total = last_bar['high'] - last_bar['low']
    body_size = abs(last_bar['close'] - last_bar['open'])

    if last_bar['volume'] > 2 * avg_volume:
        if range_total > 0 and (body_size / range_total) < 0.3:
            # Potential absorption.
            # Determine direction: if close is in upper 50% of bar, could be bullish absorption.
            mid_point = (last_bar['high'] + last_bar['low']) / 2
            return 1 if last_bar['close'] > mid_point else -1

    return 0

def check_liquidity_sweep(df):
    """
    Pillar 2: Liquidity Sweep
    - Look back 10 bars. Find highest high and lowest low.
    - Sweep high: breaks above high but closes below it -> SELL (-1)
    - Sweep low: breaks below low but closes above it -> BUY (1)
    """
    if len(df) < 11:
        return 0

    lookback_df = df.iloc[-11:-1]
    hh = lookback_df['high'].max()
    ll = lookback_df['low'].min()

    last_bar = df.iloc[-1]

    # Sweep High (SELL)
    if last_bar['high'] > hh and last_bar['close'] < hh:
        return -1

    # Sweep Low (BUY)
    if last_bar['low'] < ll and last_bar['close'] > ll:
        return 1

    return 0

def calculate_cvd(ticks):
    """
    Pillar 3: CVD
    - Tick-by-tick cumulative volume delta using vectorized operations.
    """
    if ticks is None or ticks.empty:
        return None

    # Vectorized calculation of volume delta
    delta = pd.Series(0, index=ticks.index, dtype=float)

    buy_mask = (ticks['flags'] & mt5.TICK_FLAG_BUY).astype(bool)
    sell_mask = (ticks['flags'] & mt5.TICK_FLAG_SELL).astype(bool)

    delta.loc[buy_mask] = ticks.loc[buy_mask, 'volume']
    delta.loc[sell_mask] = -ticks.loc[sell_mask, 'volume']

    # Fallback for ticks without clear buy/sell flags
    remaining_mask = ~(buy_mask | sell_mask)
    if remaining_mask.any() and 'last' in ticks.columns:
        last_above_ask = (ticks['last'] >= ticks['ask']) & remaining_mask
        last_below_bid = (ticks['last'] <= ticks['bid']) & remaining_mask
        delta.loc[last_above_ask] = ticks.loc[last_above_ask, 'volume']
        delta.loc[last_below_bid] = -ticks.loc[last_below_bid, 'volume']

    return delta.cumsum().tolist()
