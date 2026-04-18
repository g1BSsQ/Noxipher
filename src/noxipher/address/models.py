"""Address models."""

from pydantic import BaseModel

from noxipher.core.config import Network


class MidnightAddress(BaseModel):
    """Parsed Midnight address."""

    address_string: str
    address_type: str  # "unshielded" | "shielded" | "dust"
    network: Network
    payload: bytes

    class Config:
        arbitrary_types_allowed = True
