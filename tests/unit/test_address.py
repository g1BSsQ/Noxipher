"""Unit tests for address validator."""
from noxipher.address.bech32m import encode_address
from noxipher.address.validator import (
    get_address_type,
    validate_address_for_network,
)
from noxipher.core.config import Network


class TestAddressValidator:
    """Test address validation."""

    def test_validate_for_correct_network(self) -> None:
        addr = encode_address(bytes(32), "unshielded", Network.PREPROD)
        assert validate_address_for_network(addr, Network.PREPROD) is True

    def test_validate_for_wrong_network(self) -> None:
        addr = encode_address(bytes(32), "unshielded", Network.PREPROD)
        assert validate_address_for_network(addr, Network.MAINNET) is False

    def test_get_address_type(self) -> None:
        addr = encode_address(bytes(64), "shielded", Network.PREVIEW)
        assert get_address_type(addr) == "shielded"
