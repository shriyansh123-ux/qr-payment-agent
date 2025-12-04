def compute_fees(base_home: float) -> dict:
    """
    Compute markup + network fee in home currency.
    """
    markup = base_home * 0.03     # 3% markup
    network_fee = 11.0            # flat fee
    return {
        "markup_home": markup,
        "network_fee_home": network_fee,
    }
