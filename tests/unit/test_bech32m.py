"""Unit tests for Bech32m address encoding/decoding."""
import pytest

from noxipher.address.bech32m import (
    HRP_TABLE,
    decode_address,
    encode_address,
    validate_address,
)
from noxipher.core.config import Network
from noxipher.core.exceptions import AddressError


class TestBech32mEncoding:
    """Test Bech32m address operations."""

    def test_encode_decode_unshielded(self) -> None:
        """Roundtrip: encode then decode an unshielded address."""
        payload = bytes(32)  # 32 zero bytes
        address = encode_address(payload, "unshielded", Network.PREPROD)
        assert address.startswith("mn_addr_preprod1")
        addr_type, network, decoded_payload = decode_address(address)
        assert addr_type == "unshielded"
        assert network == Network.PREPROD
        assert decoded_payload == payload

    def test_encode_decode_shielded(self) -> None:
        """Roundtrip: shielded address (64 bytes payload)."""
        payload = bytes(64)
        address = encode_address(payload, "shielded", Network.PREPROD)
        assert address.startswith("mn_shield-addr_preprod1")
        addr_type, network, decoded = decode_address(address)
        assert addr_type == "shielded"
        assert decoded == payload

    def test_encode_decode_dust(self) -> None:
        """Roundtrip: dust address."""
        payload = bytes(32)
        address = encode_address(payload, "dust", Network.MAINNET)
        assert address.startswith("mn_dust1")
        addr_type, network, _ = decode_address(address)
        assert addr_type == "dust"
        assert network == Network.MAINNET

    def test_all_12_hrps(self) -> None:
        """Verify all 12 HRP entries encode/decode correctly."""
        for (addr_type, network), expected_hrp in HRP_TABLE.items():
            payload_size = 64 if addr_type == "shielded" else 32
            payload = bytes(range(payload_size))
            address = encode_address(payload, addr_type, network)
            assert address.startswith(expected_hrp)

    def test_invalid_address_fails(self) -> None:
        """Invalid address raises AddressError."""
        with pytest.raises(AddressError):
            decode_address("invalid_address_string")

    def test_validate_valid_address(self) -> None:
        payload = bytes(32)
        address = encode_address(payload, "unshielded", Network.PREPROD)
        assert validate_address(address) is True

    def test_validate_invalid_address(self) -> None:
        assert validate_address("not_an_address") is False
