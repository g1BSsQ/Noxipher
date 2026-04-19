import pytest
from unittest.mock import AsyncMock, MagicMock
from noxipher.wallet.sync import WalletSyncer
from noxipher.wallet.wallet import MidnightWallet
from noxipher.core.config import Network

@pytest.fixture
def wallet():
    mnemonic = "abandon " * 23 + "art"
    return MidnightWallet(mnemonic, Network.PREPROD)

@pytest.fixture
def mock_indexer():
    indexer = AsyncMock()
    return indexer

@pytest.mark.asyncio
async def test_sync_unshielded(wallet, mock_indexer):
    syncer = WalletSyncer(wallet, mock_indexer)
    wallet.unshielded.get_balance = AsyncMock(return_value={"NIGHT": 1000})
    
    balance = await syncer.sync_unshielded()
    assert balance["NIGHT"] == 1000
    mock_indexer.get_utxos.assert_not_called() # wallet.unshielded.get_balance might call it internally

@pytest.mark.asyncio
async def test_sync_shielded(wallet, mock_indexer):
    syncer = WalletSyncer(wallet, mock_indexer)
    mock_indexer.connect_wallet_session = AsyncMock(return_value="session-123")
    wallet.shielded.sync_coins = AsyncMock(return_value=[{"value": 100}])
    
    coins = await syncer.sync_shielded()
    assert len(coins) == 1
    assert coins[0]["value"] == 100
    mock_indexer.connect_wallet_session.assert_called_once()
    mock_indexer.disconnect_wallet_session.assert_called_once()
