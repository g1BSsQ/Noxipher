"""
Ledger operations for Midnight.
"""
from noxipher.ledger.models import LedgerParameters


def get_initial_parameters() -> LedgerParameters:
    """Get initial ledger parameters."""
    return LedgerParameters()
