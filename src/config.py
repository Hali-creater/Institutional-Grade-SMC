import os
from dotenv import load_dotenv

load_dotenv()

def getenv(key, default=None):
    v = os.getenv(key)
    if v is None:
        return default
    return v

CONFIG = {
    'MT5_ACCOUNT': int(getenv('MT5_ACCOUNT', '0')),
    'MT5_PASSWORD': getenv('MT5_PASSWORD', ''),
    'MT5_SERVER': getenv('MT5_SERVER', ''),
    'SYMBOLS': [s.strip() for s in getenv('SYMBOLS', 'XAUUSD,EURUSD').split(',') if s.strip()],
    'RISK_PERCENT': float(getenv('RISK_PERCENT', '1.0')),
    'DEFAULT_LOT_MIN': float(getenv('DEFAULT_LOT_MIN', '0.01')),
    'DEFAULT_LOT_MAX': float(getenv('DEFAULT_LOT_MAX', '1.0')),
    'MAGIC': int(getenv('MAGIC', '20251001')),
    'TIMEFRAMES': [t.strip() for t in getenv('TIMEFRAMES', 'H1,M15,M5').split(',')],
    'LOG_LEVEL': getenv('LOG_LEVEL', 'INFO'),
    'RUN_LOOP_INTERVAL_SECONDS': int(getenv('RUN_LOOP_INTERVAL_SECONDS', '300')),
}
