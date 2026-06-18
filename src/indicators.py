from src.logger import get_logger
import MetaTrader5 as mt5
import pandas as pd

logger = get_logger('indicators')

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

def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR).
    """
    if len(df) < period + 1:
        return None

    high = df['high']
    low = df['low']
    close = df['close']

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()
    return atr.iloc[-1]

def check_liquidity_sweep(df, lookback=10, atr_period=14):
    """
    Pillar 2: Advanced Liquidity Sweep
    - Look back 10 bars. Find highest high and lowest low.
    - Sweep high: broke above high but closed below it.
    - Wick depth requirement: >= 0.3x ATR.
    - Volume spike confirmation: >= 1.5x average.
    - Reversal confirmation: previous bar (the one before the signal) was moving in direction.
    """
    if len(df) < max(lookback + 1, 21, atr_period + 1):
        return 0

    atr = calculate_atr(df, atr_period)
    if atr is None:
        return 0

    lookback_df = df.iloc[-lookback-1:-1]
    hh = lookback_df['high'].max()
    ll = lookback_df['low'].min()

    last_bar = df.iloc[-1]
    prev_bar = df.iloc[-2]

    # Volume spike (20-bar avg)
    avg_volume = df['volume'].iloc[-21:-1].mean()
    volume_spike = last_bar['volume'] >= (avg_volume * 1.5)

    # Calculate wicks
    upper_wick = last_bar['high'] - max(last_bar['open'], last_bar['close'])
    lower_wick = min(last_bar['open'], last_bar['close']) - last_bar['low']

    # Sweep High (SELL)
    sweep_high = last_bar['high'] > hh and last_bar['close'] < hh
    if sweep_high:
        wick_deep = upper_wick >= (atr * 0.3)
        # Reversal confirmation: last candle close < open (bearish) or rejection of high
        reversal = last_bar['close'] < last_bar['open']
        if wick_deep and volume_spike and reversal:
            return -1

    # Sweep Low (BUY)
    sweep_low = last_bar['low'] < ll and last_bar['close'] > ll
    if sweep_low:
        wick_deep = lower_wick >= (atr * 0.3)
        # Reversal confirmation: last candle close > open (bullish) or rejection of low
        reversal = last_bar['close'] > last_bar['open']
        if wick_deep and volume_spike and reversal:
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
