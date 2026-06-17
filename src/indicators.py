# Wrappers around smartmoneyconcepts. These helpers return objects you can use for checks.
from smartmoneyconcepts import fvg, ob, swing_highs_lows, bos_choch
from src.logger import get_logger

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
