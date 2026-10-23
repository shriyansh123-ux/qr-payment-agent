"""No provider fees can be inferred from the QR payload.

This compatibility helper deliberately refuses to invent a spread/network fee.
Retrieve an actual fee quote from the specific payment provider instead.
"""


def compute_fees(base_home: float) -> dict:
    return {
        "markup_home": None,
        "network_fee_home": None,
        "fee_status": "not_quoted",
    }
