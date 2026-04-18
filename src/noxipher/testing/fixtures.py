"""
pytest fixtures for Noxipher tests.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from noxipher.core.config import Network
from noxipher.testing.testkit import (
    TEST_MNEMONIC,
    TEST_SEED_32,
    MockProofServer,
    make_test_wallet,
)

if TYPE_CHECKING:
    from noxipher.indexer.client import IndexerClient
    from noxipher.wallet.wallet import MidnightWallet


@pytest.fixture
def mock_proof_server() -> Generator[MockProofServer, None, None]:
    """Context manager fixture for MockProofServer."""
    with MockProofServer() as mock:
        mock.setup()
        yield mock


@pytest.fixture
def test_mnemonic() -> str:
    """Test BIP39 mnemonic."""
    return TEST_MNEMONIC


@pytest.fixture
def test_seed_32() -> bytes:
    """32-byte test seed."""
    return TEST_SEED_32


@pytest.fixture
def preprod_wallet() -> MidnightWallet:
    """Wallet from test mnemonic on Preprod."""
    return make_test_wallet("preprod")


@pytest.fixture
def preview_wallet() -> MidnightWallet:
    """Wallet from test mnemonic on Preview."""
    return make_test_wallet("preview")


@pytest_asyncio.fixture
async def preprod_indexer_client() -> AsyncGenerator[IndexerClient, None]:
    """IndexerClient connected to Preprod (integration test only)."""
    from noxipher.core.config import NETWORK_CONFIGS
    from noxipher.indexer.client import IndexerClient

    config = NETWORK_CONFIGS[Network.PREPROD]
    async with IndexerClient(config) as client:
        yield client
