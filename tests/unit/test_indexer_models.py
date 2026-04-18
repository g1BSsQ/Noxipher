"""Unit tests for Indexer models."""
from noxipher.indexer.models import Block, Transaction, TransactionResult, DustGenerationStatus


class TestIndexerModels:
    """Test Indexer data models."""

    def test_block_creation(self) -> None:
        block = Block(height=100, hash="abc123")
        assert block.height == 100
        assert block.hash == "abc123"

    def test_transaction_result_normalization(self) -> None:
        """TransactionResult normalizes status to uppercase."""
        result = TransactionResult(status="success")
        assert result.status == "SUCCESS"

    def test_transaction_model(self) -> None:
        tx = Transaction(hash="deadbeef")
        assert tx.hash == "deadbeef"
        assert tx.block is None
        assert tx.unshielded_created_outputs == []

    def test_dust_generation_status(self) -> None:
        status = DustGenerationStatus(
            cardano_stake_key="stake_test1...",
            is_registered=True,
            available_dust="1000000000000",
        )
        assert status.is_registered is True
