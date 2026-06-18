import asyncio
import yaml
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus.strategy import SMCInstitutionalScalper

async def run_backtest():
    # Load config
    with open("nautilus/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Create engine
    engine = BacktestEngine()

    # Configure engine
    engine_config = BacktestConfig(
        initial_capital=[{"currency": "USD", "amount": config.get("initial_capital", 10000.0)}]
    )
    # engine.configure(config=engine_config) # In newer versions configuration might be different

    # Add strategy
    strategy_config = {
        "pair_a": config.get("pair_a"),
        "entry_threshold": config.get("entry_threshold", 2),
        "risk_percent": config.get("risk_percent", 1.0),
        "lookback_bars": config.get("lookback_bars", 50),
        "timeframe": config.get("timeframe", "1-MINUTE")
    }

    # Note: Strategy config in Nautilus often uses a Config class
    engine.add_strategy(SMCInstitutionalScalper, strategy_config)

    # Run
    # await engine.run()

    # Print performance
    # report = engine.portfolio.performance()
    # print(report)

if __name__ == "__main__":
    asyncio.run(run_backtest())
