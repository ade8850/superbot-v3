import traceback

from strategy_common.ioc import container
strategy = container.strategy()


def calculate_pnl(price=None, margin=None, side=None, leverage=None, fee=None, entry_price=None) -> float:
    subject = strategy.get_subject()
    if price is None:
        price = subject.get("price")
    if margin is None:
        margin = subject.get("margin", default=100)
    if side is None:
        side = subject.get("action")
    if leverage is None:
        leverage = strategy.leverage
    if fee is None:
        fee = strategy.fee
    if entry_price is None:
        entry_price = subject.get("action_entry_price")

    try:
    # Calculate the total value of the position including leverage
        position_value: float = margin * leverage

        # Calculate the fee applied to open and close the position
        total_fee: float = position_value * fee * 2  # Fee for opening and closing

        # Calculate profit or loss
        if side == 'Buy':
            profit_or_loss = ((price - entry_price) / entry_price) * position_value
        elif side == 'Sell':
            profit_or_loss = ((entry_price - price) / entry_price) * position_value
        else:
            profit_or_loss = 0

        # Adjust profit or loss by subtracting the total fees
        adjusted_profit_or_loss: float = profit_or_loss - total_fee

        return adjusted_profit_or_loss
    except Exception as ex:
        traceback.print_exc()
        return -1


