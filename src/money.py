"""Currency minor units and Decimal rounding helpers.

Amounts stay as ``Decimal`` inside the app. They are only turned into JSON
numbers at the API boundary, after rounding to the currency's real minor unit.
"""
from decimal import ROUND_HALF_UP, Decimal

# ISO 4217 currencies whose minor unit is not 2 decimal places.
_ZERO_DECIMAL = frozenset({
    "BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW", "PYG",
    "RWF", "UGX", "UYI", "VND", "VUV", "XAF", "XOF", "XPF",
})
_THREE_DECIMAL = frozenset({"BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"})


def minor_units(currency: str) -> int:
    """Number of decimal places used by ``currency`` (defaults to 2)."""
    code = (currency or "").upper()
    if code in _ZERO_DECIMAL:
        return 0
    if code in _THREE_DECIMAL:
        return 3
    return 2


def quantize(amount: Decimal, currency: str) -> Decimal:
    """Round ``amount`` half-up to the minor unit of ``currency``."""
    return amount.quantize(Decimal(1).scaleb(-minor_units(currency)), rounding=ROUND_HALF_UP)
