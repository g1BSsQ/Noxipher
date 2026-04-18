"""
Shielded token utilities.

Shielded tokens = NIGHT wrapped in ZSwap privacy layer.
Token type hex prefix: "010001..." (verify from ledger-v8)
"""

SHIELDED_TOKEN_TYPE_PREFIX = bytes.fromhex("010001")


def is_shielded_token(token_type_bytes: bytes) -> bool:
    """Check if token type is a shielded token."""
    return token_type_bytes[:3] == SHIELDED_TOKEN_TYPE_PREFIX


class ShieldedToken:
    """Shielded token type descriptor."""

    TYPE_PREFIX = SHIELDED_TOKEN_TYPE_PREFIX
    SYMBOL = "sNIGHT"
    IS_PRIVATE = True
