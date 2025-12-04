def get_fx_rate(local_currency: str, home_currency: str = "INR") -> float:
    """
    Return a mock FX rate for demo.
    """
    if local_currency == home_currency:
        return 1.0
    if local_currency == "JPY" and home_currency == "INR":
        return 0.55  # mock example
    if local_currency == "USD" and home_currency == "INR":
        return 83.0
    return 1.0
