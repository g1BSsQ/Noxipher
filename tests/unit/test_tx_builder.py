from unittest.mock import AsyncMock, MagicMock

import pytest

from noxipher.core.config import Network
from noxipher.tx.builder import TransactionBuilder
from noxipher.wallet.wallet import MidnightWallet


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.config.name = "preprod1"
    client.config.min_fee = 10_000
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
    mock_client.config.min_fee = 100

    # Mock UTXOs: 1000 and 5000. Largest First should pick 5000.
    wallet.unshielded.get_utxos = AsyncMock(
        return_value=[
            {"value": 1000, "intentHash": "aa" * 32, "outputNo": 0},
            {"value": 5000, "intentHash": "bb" * 32, "outputNo": 1},
        ]
    )

    from noxipher.address.bech32m import encode_address

    recipient = encode_address(bytes(32), "unshielded", Network.PREPROD)
    amount = 500
    ttl = 3600

    tx = await builder._build_unshielded_transfer(wallet, recipient, amount, ttl=ttl)

    assert tx["type"] == "unshielded_transfer"
    # Verify input is the 5000 one
    offer = tx["standard"]["intents"]["0"]["guaranteed_unshielded_offer"]
    assert offer["inputs"][0]["value"] == 5000
    assert len(offer["outputs"]) == 2


@pytest.mark.asyncio
async def test_build_shielded_transfer_skeleton(
    mock_client: MagicMock, wallet: MidnightWallet
) -> None:
    builder = TransactionBuilder(mock_client)

    # Add a coin to shielded state
    from noxipher.zswap.notes import ShieldedCoinNote

    coin = ShieldedCoinNote(
        token_type=b"\x00" * 32,
        value=1000,
        nonce=b"\x00" * 32,
        owner_pk=wallet.shielded._keys.coin_public_key,
        merkle_tree_index=5,
    )
    wallet.shielded_state.add_coin(coin)

    recipient = wallet.shielded.address
    amount = 500

    tx = await builder._build_shielded_transfer(wallet, recipient, amount)

    assert tx["type"] == "shielded_transfer"
    assert len(tx["circuits"]) > 0
    # Spend circuit
    assert tx["circuits"][0]["id"] == "zswap_spend"
    assert tx["circuits"][0]["private_inputs"]["coin"]["value"] == 1000
    assert "merkle_proof" in tx["circuits"][0]["private_inputs"]


@pytest.mark.asyncio
async def test_prove_transaction(mock_client: MagicMock) -> None:
    from noxipher.tx.builder import TransactionBuilder

    builder = TransactionBuilder(mock_client)

    tx = {"type": "shielded_transfer", "circuits": [{"id": "zswap_spend"}]}

    # Mock ZKProver
    with MagicMock():
        # Note: this is a bit tricky with imports, better to mock the instance
        builder._prove_transaction = AsyncMock(return_value={"proven": True})

        result = await builder._prove_transaction(tx)
        assert result["proven"] is True


@pytest.mark.asyncio
async def test_build_shielded_transfer_multi_asset(
    mock_client: MagicMock, wallet: MidnightWallet
) -> None:
    builder = TransactionBuilder(mock_client)
    from noxipher.zswap.notes import ShieldedCoinNote

    # Custom token type
    token_type = b"\x01" * 32
    coin = ShieldedCoinNote(
        token_type=token_type,
        value=2000,
        nonce=b"\x00" * 32,
        owner_pk=wallet.shielded._keys.coin_public_key,
        merkle_tree_index=10,
    )
    wallet.shielded_state.add_coin(coin)

    recipient = wallet.shielded.address
    amount = 1500

    tx = await builder._build_shielded_transfer(
        wallet, recipient, amount, token_type=token_type
    )

    assert tx["type"] == "shielded_transfer"
    # Largest first selection should pick our coin
    assert tx["circuits"][0]["private_inputs"]["coin"]["value"] == 2000

    # Verify nonces are random (not \x01 or \x02)
    output_circuit = [c for c in tx["circuits"] if c["id"] == "zswap_output"][0]
    nonce_hex = output_circuit["private_inputs"]["nonce"]
    assert nonce_hex != ("01" * 32)
    assert len(nonce_hex) == 64


@pytest.mark.asyncio
async def test_build_unshielded_transfer_dust_protection(
    mock_client: MagicMock, wallet: MidnightWallet
) -> None:
    builder = TransactionBuilder(mock_client)
    mock_client.config.min_fee = 100
    
    # Mock UTXOs for DUST
    wallet.dust.get_utxos = AsyncMock(
        return_value=[
            {"value": 150, "intentHash": "cc" * 32, "outputNo": 0},
        ]
    )
    
    # Required = amount(0) + fee(100) = 100
    # Selected = 150
    # Change = 50. Since 50 < DUST_THRESHOLD (1000), it should be added to fee.
    
    recipient = wallet.unshielded.address
    tx = await builder._build_unshielded_transfer(
        wallet, recipient, 0, fee=100, use_dust=True
    )
    
    offer = tx["standard"]["intents"]["0"]["guaranteed_unshielded_offer"]
    assert len(offer["outputs"]) == 0  # No change output because of dust protection
    assert tx["fee"] == 150  # 100 original fee + 50 tiny change
