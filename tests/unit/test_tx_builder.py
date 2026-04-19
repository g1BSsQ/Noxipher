from unittest.mock import AsyncMock, MagicMock

import pytest

from noxipher.core.config import Network
from noxipher.tx.builder import TransactionBuilder
from noxipher.wallet.wallet import MidnightWallet


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.config.name = "preprod1"
    client.indexer = AsyncMock()
    return client


@pytest.fixture
def wallet() -> MidnightWallet:
    mnemonic = "abandon " * 23 + "art"
    return MidnightWallet(mnemonic, Network.PREPROD)


@pytest.mark.asyncio
async def test_build_unshielded_transfer_with_ttl(
    mock_client: MagicMock, wallet: MidnightWallet
) -> None:
    builder = TransactionBuilder(mock_client)

    # Mock UTXOs
    wallet.unshielded.get_utxos = AsyncMock(
        return_value=[{"value": 1000, "intentHash": "aa" * 32, "outputNo": 0}]
    )

    from noxipher.address.bech32m import encode_address

    recipient = encode_address(bytes(32), "unshielded", Network.PREPROD)
    amount = 500
    ttl = 3600

    tx = await builder._build_unshielded_transfer(wallet, recipient, amount, ttl=ttl)

    assert tx["type"] == "unshielded_transfer"
    assert tx["standard"]["intents"]["0"]["ttl"] == ttl
    # recipient + change
    offer = tx["standard"]["intents"]["0"]["guaranteed_unshielded_offer"]
    assert len(offer["outputs"]) == 2


@pytest.mark.asyncio
async def test_build_shielded_transfer_skeleton(
    mock_client: MagicMock, wallet: MidnightWallet
) -> None:
    builder = TransactionBuilder(mock_client)

    # Add a coin to shielded state
    from noxipher.zswap.notes import ShieldedCoinNote

    coin = ShieldedCoinNote(
        token_type=b"\x00" * 32, value=1000, nonce=b"\x00" * 32, merkle_tree_index=5
    )
    wallet.shielded_state.add_coin(coin)

    recipient = "mn_shield-addr_preprod1..."
    amount = 500

    tx = await builder._build_shielded_transfer(wallet, recipient, amount)

    assert tx["type"] == "shielded_transfer"
    assert len(tx["circuits"]) > 0
    # Spend circuit
    assert tx["circuits"][0]["id"] == "zswap_spend"
    assert tx["circuits"][0]["private_inputs"]["coin"]["value"] == 1000
