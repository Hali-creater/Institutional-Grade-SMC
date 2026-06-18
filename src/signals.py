from src.indicators import (
    check_order_absorption, check_liquidity_sweep, calculate_cvd
)
from src.logger import get_logger
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from src import data
from src.config import CONFIG
import pandas as pd

logger = get_logger('signals')

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

def check_news_events(symbol):
    """
    Checks MT5 Economic Calendar for high-impact news events.
    Returns True if a high-impact event is within the configured window.
    """
    try:
        window_mins = CONFIG.get('NEWS_FILTER_WINDOW_MINS', 30)
        now = datetime.now()
        from_date = now - timedelta(minutes=window_mins)
        to_date = now + timedelta(minutes=window_mins)

        # Get currencies for the symbol (e.g., EURUSD -> EUR, USD)
        # For simplicity, assume standard 6-char forex or 3-char metals/crypto
        # A more robust way would be mt5.symbol_info(symbol).currency_base/profit
        info = mt5.symbol_info(symbol)
        if info is None:
            return False

        currencies = [info.currency_base, info.currency_profit, "USD"] # Always include USD
        currencies = list(set(currencies)) # unique

        items = mt5.calendar_events_get(from_date=from_date, to_date=to_date)
        if items is None or len(items) == 0:
            return False

        for item in items:
            # Check importance (3 = high)
            if item.importance >= mt5.CALENDAR_IMPORTANCE_HIGH:
                if item.currency in currencies:
                    logger.warning(f"High-impact news event detected: {item.event_name} ({item.currency}) at {datetime.fromtimestamp(item.time)}")
                    return True
        return False
    except Exception as e:
        logger.error(f"Error checking calendar: {e}")
        return False

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
