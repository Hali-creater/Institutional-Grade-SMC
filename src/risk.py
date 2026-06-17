from src.logger import get_logger

logger = get_logger('risk')

def compute_lot_from_risk(mt5, symbol, balance, risk_percent, stop_loss_price):
    """Approximate lot calculation:
    - Attempts to use MT5 symbol info for accurate tick/trade values.
    - Falls back to a rough pip-value assumption if necessary.
    """
    try:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError('symbol info not found')
        point = info.point
        contract_size = getattr(info, 'trade_contract_size', None) or getattr(info, 'contract_size', None) or 100000
        # risk amount in USD
        risk_amount = (risk_percent/100.0) * balance
        price_diff = float(stop_loss_price)
        approx_risk_per_lot = price_diff * contract_size
        if approx_risk_per_lot <= 0:
            approx_risk_per_lot = 1.0
        lot = risk_amount / approx_risk_per_lot
        if lot < 0.01:
            lot = 0.01
        logger.info('Computed lot=%s using balance=%s risk_amount=%s price_diff=%s contract_size=%s', lot, balance, risk_amount, price_diff, contract_size)
        return round(lot, 2)
    except Exception as e:
        logger.error('compute_lot_from_risk error: %s', e)
        return 0.01
