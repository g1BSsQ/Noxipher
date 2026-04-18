"""
MidnightTestkit — utilities for unit and integration tests.

Fixtures:
  - MockProofServer: respx mock for Proof Server HTTP
  - MockIndexerResponses: mock GraphQL responses
  - TEST_MNEMONIC: deterministic test mnemonic
  - TEST_SEED: all-zeros 32-byte seed (for fast unit tests)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noxipher.wallet.wallet import MidnightWallet

import httpx
import respx

# All-zeros mnemonic (BIP39 test vector)
# "abandon abandon abandon ... art" (24 words)
TEST_MNEMONIC = "abandon " * 23 + "art"

# All-zeros 32-byte seed
TEST_SEED_32 = bytes(32)

# Test network
TEST_NETWORK = "preprod"


class MockProofServer:
    """
    Mock Proof Server for unit tests.
    Uses respx to intercept httpx calls.
    """

    def __init__(self) -> None:
        self._router = respx.MockRouter()

    def setup(self) -> None:
        """Setup mock routes."""
        # GET /health → version info
        self._router.get("/health").mock(
            return_value=httpx.Response(
                200,
                json={"status": "ok", "version": "8.0.3"},
            )
        )

        # POST /prove → fake proof bytes
        self._router.post("/prove").mock(
            return_value=httpx.Response(
                200,
                content=bytes(128),  # 128 zero bytes = fake proof
            )
        )

    def __enter__(self) -> MockProofServer:
        self._router.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._router.stop()


class MockIndexerResponses:
    """Preset GraphQL responses for testing."""

    @staticmethod
    def empty_block(height: int = 1) -> dict:
        """Empty block response."""
        return {
            "block": {
                "height": height,
                "hash": "a" * 64,
                "parent_hash": "b" * 64,
                "timestamp": "2026-04-18T00:00:00Z",
            }
        }

    @staticmethod
    def empty_transaction_list() -> dict:
        """Empty transaction list."""
        return {"transactions": {"nodes": []}}

    @staticmethod
    def transaction_finalized(tx_hash: str) -> dict:
        """Finalized transaction response."""
        return {
            "transactions": {
                "nodes": [
                    {
                        "hash": tx_hash,
                        "block": {"height": 100, "hash": "c" * 64},
                        "transaction_result": {
                            "status": "success",
                            "segments": [],
                        },
                        "fees": {"paid_fees": "1000000000000"},
                        "raw": "0x" + "00" * 64,
                    }
                ]
            }
        }


def make_test_wallet(network: str = "preprod") -> MidnightWallet:
    """
    Create MidnightWallet from test mnemonic.
    Deterministic — same keys every time.
    """
    from noxipher.core.config import Network
    from noxipher.wallet.wallet import MidnightWallet

    return MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network(network))
