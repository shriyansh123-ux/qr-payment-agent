"""Manual reference conversion; independent of QR parsing and payment routing."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from src.api.deps import api_key_or_public_demo
from src.services import currencies
from src.services.fx import FXRateService, FXUnavailable

router = APIRouter(tags=["currency-converter"])
_fx = FXRateService()


class ConversionRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=1000000000000, max_digits=19, decimal_places=6)
    from_currency: str = Field(pattern=r"^[A-Z]{3}$")
    to_currency: str = Field(pattern=r"^[A-Z]{3}$")


@router.get("/api/currencies")
def list_currencies():
    try:
        return {"currencies": currencies.supported_currencies(), "source": "frankfurter-reference"}
    except FXUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


def _convert(body: ConversionRequest) -> dict:
    codes = currencies.supported_codes()
    if body.from_currency not in codes or body.to_currency not in codes:
        raise HTTPException(422, "Choose currencies from the supported list.")
    return _fx.convert(body.amount, body.from_currency, body.to_currency)


@router.post("/api/convert", dependencies=[Depends(api_key_or_public_demo)])
async def convert(body: ConversionRequest):
    try:
        result = await run_in_threadpool(_convert, body)
    except FXUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"amount": str(body.amount), **result}
