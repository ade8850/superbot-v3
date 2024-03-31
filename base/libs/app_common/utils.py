import traceback


def calculate_pnl(margin, side, leverage, fee, entry_price, cur_price) -> float:
    try:
    # Calculate the total value of the position including leverage
        position_value: float = margin * leverage

        # Calculate the fee applied to open and close the position
        total_fee: float = position_value * fee * 2  # Fee for opening and closing

        # Calculate profit or loss
        if side == 'Buy':
            profit_or_loss = ((cur_price - entry_price) / entry_price) * position_value
        elif side == 'Sell':
            profit_or_loss = ((entry_price - cur_price) / entry_price) * position_value
        else:
            raise ValueError("Side must be either 'Buy' or 'Sell'")

        # Adjust profit or loss by subtracting the total fees
        adjusted_profit_or_loss: float = profit_or_loss - total_fee

        return adjusted_profit_or_loss
    except Exception as ex:
        traceback.print_exc()
        return -1


