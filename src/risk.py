from src.logger import get_logger

logger = get_logger('risk')

def compute_lot_from_risk(mt5, symbol, balance, risk_percent, sl_distance):
    """Approximate lot calculation:
    - Risk only 1% of your account per trade.
    - Risk = Balance * risk_percent
    - sl_distance = abs(entry_price - stop_loss_price)
    """
    try:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError('symbol info not found')

        contract_size = getattr(info, 'trade_contract_size', None) or getattr(info, 'contract_size', None) or 100000

        # risk amount in account currency
        risk_amount = (risk_percent/100.0) * balance

        # If sl_distance is in points/price, we need to know the value of 1 point in account currency
        # For simplicity, we use: lot = risk_amount / (sl_distance * contract_size)
        # This assumes the quote currency is the same as the account currency.

        if sl_distance <= 0:
            logger.warning("SL distance is 0 or negative, using minimal lot.")
            return 0.01

        lot = risk_amount / (sl_distance * contract_size)

        # Clamp to symbol limits
        lot_step = info.volume_step
        lot = round(lot / lot_step) * lot_step

        if lot < info.volume_min:
            lot = info.volume_min
        if lot > info.volume_max:
            lot = info.volume_max

        logger.info('Computed lot=%s using balance=%s risk_amount=%s sl_distance=%s contract_size=%s', lot, balance, risk_amount, sl_distance, contract_size)
        return round(lot, 2)
    except Exception as e:
        logger.error('compute_lot_from_risk error: %s', e)
        return 0.01
