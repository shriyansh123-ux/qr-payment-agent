import logging
from typing import Optional

from src.tools.fx_live_api_tool import get_live_fx_rate

logger = logging.getLogger(__name__)

# Same economics as before:
# - 3% FX markup
# - Flat 11 INR network fee
MARKUP_PERCENT = 0.03
NETWORK_FEE_HOME = 11.0

# Fallback mock rates for when live API fails or for specific test currencies
MOCK_RATES = {
    ("JPY", "INR"): 0.55,
    ("USD", "INR"): 83.0,
    ("THB", "INR"): 1.0,
    ("EUR", "INR"): 1.0,
}


class FXRateAgent:
    """
    Computes FX conversion from local_currency into home_currency.

    Primary path:
        - Try live rate from exchangerate.host
    Fallback:
        - Use MOCK_RATES mapping (your old hackathon values)
        - Or a generic default (80.0) if nothing matches
    """

    def _pick_rate(
        self,
        amount_local: float,
        local_currency: str,
        home_currency: str,
    ) -> tuple[float, str, str]:
        """
        Decide which FX rate to use:
        - Try live FX first
        - If live fails, fall back to mock
        Returns:
            (rate, provider, notes)
        """
        local_currency = local_currency.upper()
        home_currency = home_currency.upper()

        # Same-currency shortcut
        if local_currency == home_currency:
            return 1.0, "same-currency", "No FX conversion needed (same currency)."

        # 1) Try live FX
        live_rate: Optional[float] = get_live_fx_rate(local_currency, home_currency)
        if live_rate:
            logger.info(
                "Using live FX rate: %s -> %s = %f",
                local_currency,
                home_currency,
                live_rate,
            )
            return (
                live_rate,
                "exchangerate.host-live",
                "Live FX rate from exchangerate.host with standard markup.",
            )

        # 2) Fallback to mock rates (old behavior)
        key = (local_currency, home_currency)
        if key in MOCK_RATES:
            rate = MOCK_RATES[key]
            logger.warning(
                "Live FX failed, using mock rate for %s -> %s: %f",
                local_currency,
                home_currency,
                rate,
            )
            return (
                rate,
                "mock-fx",
                "Standard Asia-Pacific FX markup (mock fallback).",
            )

        # 3) Last-resort generic default
        default_rate = 80.0
        logger.error(
            "Live FX failed and no specific mock rate for %s -> %s; using default %f",
            local_currency,
            home_currency,
            default_rate,
        )
        return (
            default_rate,
            "mock-fx-default",
            "Generic fallback FX rate with standard markup.",
        )

    def handle(
        self,
        amount_local: float,
        local_currency: str,
        home_currency: str,
    ) -> dict:
        """
        Main entry point: compute FX breakdown.

        Returns dict:
            {
              "from_currency": ...,
              "to_currency": ...,
              "rate": ...,
              "base_home": ...,
              "markup_home": ...,
              "network_fee_home": ...,
              "total_home": ...,
              "notes": ...,
              "provider": ...,
            }
        """
        local_currency = local_currency.upper()
        home_currency = home_currency.upper()

        rate, provider, notes = self._pick_rate(
            amount_local, local_currency, home_currency
        )

        base_home = amount_local * rate
        markup_home = base_home * MARKUP_PERCENT
        network_fee_home = NETWORK_FEE_HOME
        total_home = base_home + markup_home + network_fee_home

        return {
            "from_currency": local_currency,
            "to_currency": home_currency,
            "rate": rate,
            "base_home": base_home,
            "markup_home": markup_home,
            "network_fee_home": network_fee_home,
            "total_home": total_home,
            "notes": notes,
            "provider": provider,
        }
