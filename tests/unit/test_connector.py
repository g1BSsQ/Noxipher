from unittest.mock import AsyncMock, MagicMock

import pytest

from noxipher.dapp.connector import DAppConnector
from noxipher.wallet.wallet import MidnightWallet


@pytest.fixture
def mock_wallet() -> MidnightWallet:
    wallet = MagicMock(spec=MidnightWallet)
    wallet.unshielded.public_key = b"pubkey"
    return wallet


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.indexer = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_balance_transaction_adds_inputs(
    mock_client: MagicMock, mock_wallet: MidnightWallet
) -> None:
    connector = DAppConnector(mock_wallet, mock_client)

    unbound_tx = {
        "standard": {
            "intents": {
                "0": {
                    "guaranteed_unshielded_offer": {
                        "inputs": [],
                        "outputs": [{"value": 5000, "owner": b"recipient", "type_": 0}],
                    }
                }
            }
        }
    }

    # Mock UTXOs: one UTXO of 20000
    mock_wallet.unshielded.get_utxos = AsyncMock(
        return_value=[{"value": 20000, "intentHash": "aa" * 32, "outputNo": 0}]
    )

    balanced = await connector.balance_transaction(unbound_tx)

    offer = balanced["standard"]["intents"]["0"]["guaranteed_unshielded_offer"]
    assert len(offer["inputs"]) == 1
    assert offer["inputs"][0]["value"] == 20000
    # 20000 - (5000 + 10000 fee) = 5000 change
    assert len(offer["outputs"]) == 2
    assert offer["outputs"][1]["value"] == 5000


@pytest.mark.asyncio
async def test_balance_transaction_insufficient_funds(
    mock_client: MagicMock, mock_wallet: MidnightWallet
) -> None:
    from noxipher.core.exceptions import TransactionError

    connector = DAppConnector(mock_wallet, mock_client)

    unbound_tx = {
        "standard": {
            "intents": {
                "0": {
                    "guaranteed_unshielded_offer": {
                        "inputs": [],
                        "outputs": [{"value": 5000, "owner": b"recipient", "type_": 0}],
                    }
                }
            }
        }
    }

    # Mock UTXOs: only 1000
    mock_wallet.unshielded.get_utxos = AsyncMock(
        return_value=[{"value": 1000, "intentHash": "aa" * 32, "outputNo": 0}]
    )

    with pytest.raises(TransactionError, match="Insufficient funds"):
        await connector.balance_transaction(unbound_tx)
