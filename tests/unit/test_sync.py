from unittest.mock import AsyncMock

import pytest

from noxipher.core.config import Network
from noxipher.wallet.sync import WalletSyncer
from noxipher.wallet.wallet import MidnightWallet


@pytest.fixture
def wallet() -> MidnightWallet:
    mnemonic = "abandon " * 23 + "art"
    return MidnightWallet(mnemonic, Network.PREPROD)


@pytest.fixture
def mock_indexer() -> AsyncMock:
    indexer = AsyncMock()
    return indexer


@pytest.mark.asyncio
async def test_sync_unshielded(wallet: MidnightWallet, mock_indexer: AsyncMock) -> None:
    syncer = WalletSyncer(wallet, mock_indexer)
    wallet.unshielded.get_balance = AsyncMock(return_value={"NIGHT": 1000})

    balance = await syncer.sync_unshielded()
    assert balance["NIGHT"] == 1000
    # wallet.unshielded.get_balance might call it internally
    mock_indexer.get_utxos.assert_not_called()


@pytest.mark.asyncio
async def test_sync_shielded(wallet: MidnightWallet, mock_indexer: AsyncMock) -> None:
    syncer = WalletSyncer(wallet, mock_indexer)
    mock_indexer.connect_wallet_session = AsyncMock(return_value="session-123")
    wallet.shielded.sync_coins = AsyncMock(return_value=[{"value": 100}])

    coins = await syncer.sync_shielded()
    assert len(coins) == 1
    assert coins[0]["value"] == 100
    mock_indexer.connect_wallet_session.assert_called_once()
    mock_indexer.disconnect_wallet_session.assert_called_once()
