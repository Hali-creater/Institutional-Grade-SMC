import MetaTrader5 as mt5
from src.logger import get_logger
logger = get_logger('executor')

def connect_and_login(account, password, server):
    if not mt5.initialize():
        logger.error('MT5 initialize failed')
        return False
    ok = mt5.login(account, password, server)
    if not ok:
        logger.error('MT5 login failed: %s', ok)
        mt5.shutdown()
        return False
    logger.info('Logged in to MT5 Account')
    return True

def place_limit_order(symbol, lot, price, sl, tp, magic=0, comment='SMC Limit'):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logger.error('No tick for symbol %s', symbol)
        return None
    ask = tick.ask
    bid = tick.bid
    action = mt5.TRADE_ACTION_PENDING
    order_type = mt5.ORDER_TYPE_BUY_LIMIT if price < ask else mt5.ORDER_TYPE_SELL_LIMIT if price > bid else mt5.ORDER_TYPE_BUY
    request = {
        'action': action,
        'symbol': symbol,
        'volume': float(lot),
        'type': order_type,
        'price': float(price),
        'sl': float(sl),
        'tp': float(tp),
        'deviation': 20,
        'magic': magic,
        'comment': comment,
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN
    }
    result = mt5.order_send(request)
    logger.info('Place limit order result: %s', result)
    return result

def place_market_order(symbol, lot, side, sl, tp, magic=0, comment='SMC Market'):
    order_type = mt5.ORDER_TYPE_BUY if side.lower()=='buy' else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': float(lot),
        'type': order_type,
        'price': price,
        'sl': float(sl),
        'tp': float(tp),
        'deviation': 20,
        'magic': magic,
        'comment': comment,
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN
    }
    result = mt5.order_send(request)
    logger.info('Place market order result: %s', result)
    return result

def close_positions(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return None
    for pos in positions:
        order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask
        close_request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': pos.volume,
            'type': order_type,
            'position': pos.ticket,
            'price': price,
            'deviation': 20,
            'magic': pos.magic,
            'comment': 'Close by bot',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_RETURN
        }
        result = mt5.order_send(close_request)
        logger.info('Close result: %s', result)
    return True
