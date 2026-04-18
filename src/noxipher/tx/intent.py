"""Transaction intent types."""

from typing import Any

from pydantic import BaseModel


from noxipher.tx.offer import ZswapOffer


class ContractCallPrototype(BaseModel):
    """Prototype for a contract call."""

    contract_address: str
    entry_point: str
    args: dict[str, Any] = {}



class Intent(BaseModel):
    """Contract call intent — fallible segment."""

    contract_address: str
    entry_point: str
    guaranteed_offer: ZswapOffer = ZswapOffer()
    fallible_offer: ZswapOffer = ZswapOffer()
