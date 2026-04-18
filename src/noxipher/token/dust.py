"""
DUST token utilities.

DUST is a shielded, non-transferable fee resource.
Generated automatically from NIGHT UTxOs after registration.
"""

DUST_ADDITIONAL_FEE_OVERHEAD = 300_000_000_000_000  # Specks per transaction
DUST_FEE_BLOCKS_MARGIN = 5  # extra blocks buffer


class DUSTToken:
    """DUST token descriptor."""

    SYMBOL = "DUST"
    IS_TRANSFERABLE = False
    ADDITIONAL_FEE_OVERHEAD = DUST_ADDITIONAL_FEE_OVERHEAD
    FEE_BLOCKS_MARGIN = DUST_FEE_BLOCKS_MARGIN

    @staticmethod
    def estimate_tx_cost(base_gas: int) -> int:
        """
        Estimate DUST cost for a transaction.
        DUST cost = base_gas + additionalFeeOverhead
        """
        return base_gas + DUST_ADDITIONAL_FEE_OVERHEAD
