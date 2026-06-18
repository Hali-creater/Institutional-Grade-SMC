from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar, Tick
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.objects import Quantity
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path so we can import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import indicators, signals, risk

class SMCInstitutionalScalper(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.get("pair_a", "EURUSD.SIM"))
        self.entry_threshold = config.get("entry_threshold", 2)
        self.risk_percent = config.get("risk_percent", 1.0)
        self.lookback_bars = config.get("lookback_bars", 50)
        self.timeframe = config.get("timeframe", "1-MINUTE")

        self.bar_data = []
        self.tick_data = []

    def on_start(self):
        self.subscribe_bars(self.instrument_id, self.timeframe)
        self.subscribe_ticks(self.instrument_id)
        self.info(f"Strategy started for {self.instrument_id}")

    def on_bar(self, bar: Bar):
        self.bar_data.append({
            'time': pd.to_datetime(bar.ts_event, unit='ns'),
            'open': bar.open.as_double(),
            'high': bar.high.as_double(),
            'low': bar.low.as_double(),
            'close': bar.close.as_double(),
            'volume': bar.volume.as_double()
        })

        if len(self.bar_data) > self.lookback_bars:
            self.bar_data.pop(0)

        if len(self.bar_data) < self.lookback_bars:
            return

        # Adapt to pandas DataFrame for existing indicators
        df = pd.DataFrame(self.bar_data)

        # Pillar 1: Absorption
        p1 = indicators.check_order_absorption(df)

        # Pillar 2: Advanced Sweep
        p2 = indicators.check_liquidity_sweep(df)

        # Pillar 3: CVD Divergence
        p3 = self._check_cvd_divergence(df)

        # Confluence score
        buy_score = (1 if p1 == 1 else 0) + (1 if p2 == 1 else 0) + (1 if p3 == 1 else 0)
        sell_score = (1 if p1 == -1 else 0) + (1 if p2 == -1 else 0) + (1 if p3 == -1 else 0)

        if not self.has_position():
            if buy_score >= self.entry_threshold:
                self._enter_trade(OrderSide.BUY, bar, df)
            elif sell_score >= self.entry_threshold:
                self._enter_trade(OrderSide.SELL, bar, df)

    def on_tick(self, tick: Tick):
        self.tick_data.append({
            'time': pd.to_datetime(tick.ts_event, unit='ns'),
            'bid': tick.bid.as_double() if tick.bid else 0,
            'ask': tick.ask.as_double() if tick.ask else 0,
            'last': tick.last.as_double() if tick.last else 0,
            'volume': tick.volume.as_double() if tick.volume else 0,
            'flags': 0
        })

        # Keep last 10 minutes of ticks
        cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(minutes=10)
        self.tick_data = [t for t in self.tick_data if t['time'] > cutoff]

    def _check_cvd_divergence(self, df_m1):
        if not self.tick_data:
            return 0

        ticks_df = pd.DataFrame(self.tick_data)
        cvd_values = indicators.calculate_cvd(ticks_df)
        if not cvd_values:
            return 0

        cvd_start = cvd_values[0]
        cvd_end = cvd_values[-1]
        cvd_trend = 1 if cvd_end > cvd_start else -1 if cvd_end < cvd_start else 0

        price_start = df_m1['close'].iloc[-5]
        price_end = df_m1['close'].iloc[-1]
        price_trend = 1 if price_end > price_start else -1 if price_end < price_start else 0

        if cvd_trend == 1 and price_trend <= 0:
            return 1
        if cvd_trend == -1 and price_trend >= 0:
            return -1
        return 0

    def _enter_trade(self, side, bar, df):
        instrument = self.cache.instrument(self.instrument_id)

        # Simple risk management for demonstration in Nautilus
        equity = float(self.portfolio.account(instrument.quote_currency).balance_total)
        risk_amount = equity * (self.risk_percent / 100.0)

        # Calculate SL/TP distances
        atr = indicators.calculate_atr(df)
        sl_dist = atr * 2 # Example SL distance

        # Calculate quantity (lot size)
        # Nautilus uses Quantity objects
        qty = risk_amount / (sl_dist * instrument.contract_size)
        quantity = instrument.make_quantity(qty)

        # Place market order
        order = self.order_factory.market_order(
            instrument_id=self.instrument_id,
            side=side,
            quantity=quantity,
        )
        self.submit_order(order)
        self.info(f"Submitted {side} market order for {quantity} {self.instrument_id}")

    def has_position(self):
        return len(self.portfolio.positions(self.instrument_id)) > 0
