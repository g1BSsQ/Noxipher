"""
NIGHT token utilities.

NIGHT = native unshielded token of Midnight.
RawTokenType = bytes(32) (all zeros — confirmed from ledger-v8)
Total supply: 24,000,000,000 NIGHT
Unit: Specks (smallest unit)
"""

from __future__ import annotations

# NIGHT native token type (32 zero bytes)
NIGHT_TOKEN_TYPE = bytes(32)

# Token type hex (for Indexer queries)
NIGHT_TOKEN_TYPE_HEX = "00" * 32

# Specks per NIGHT (hypothesis — verify from ledger-v8)
SPECKS_PER_NIGHT = 1_000_000


def specks_to_night(specks: int) -> float:
    """
    Convert Specks → NIGHT.

    ⚠️ Ratio needs verification from ledger-v8 (hypothesis: 1 NIGHT = 1_000_000 Specks)
    """
    return specks / SPECKS_PER_NIGHT


def night_to_specks(night: float) -> int:
    """Convert NIGHT → Specks."""
    return int(night * SPECKS_PER_NIGHT)


class NIGHTToken:
    """NIGHT token type descriptor."""

    RAW_TYPE = NIGHT_TOKEN_TYPE
    RAW_TYPE_HEX = NIGHT_TOKEN_TYPE_HEX
    SYMBOL = "NIGHT"
    DECIMALS = 6  # hypothesis — verify
    TOTAL_SUPPLY_SPECKS = 24_000_000_000 * SPECKS_PER_NIGHT
