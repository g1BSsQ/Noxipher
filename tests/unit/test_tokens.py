"""Unit tests for token models."""
from noxipher.token.night import NIGHTToken, specks_to_night, night_to_specks
from noxipher.token.dust import DUSTToken
from noxipher.token.shielded import ShieldedToken


class TestNIGHTToken:
    """Test NIGHT token utilities."""

    def test_token_type_is_32_zero_bytes(self) -> None:
        assert NIGHTToken.RAW_TYPE == bytes(32)
        assert len(NIGHTToken.RAW_TYPE_HEX) == 64

    def test_specks_conversion(self) -> None:
        assert night_to_specks(1.0) == 1_000_000
        assert specks_to_night(1_000_000) == 1.0


class TestDUSTToken:
    """Test DUST token properties."""

    def test_not_transferable(self) -> None:
        assert DUSTToken.IS_TRANSFERABLE is False

    def test_fee_overhead(self) -> None:
        assert DUSTToken.ADDITIONAL_FEE_OVERHEAD == 300_000_000_000_000

    def test_estimate_tx_cost(self) -> None:
        cost = DUSTToken.estimate_tx_cost(1_000_000)
        assert cost == 300_000_001_000_000


class TestShieldedToken:
    """Test Shielded token properties."""

    def test_is_private(self) -> None:
        assert ShieldedToken.IS_PRIVATE is True
