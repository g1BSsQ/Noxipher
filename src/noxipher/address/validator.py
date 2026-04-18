"""Address validation utilities."""

from noxipher.address.bech32m import decode_address
from noxipher.core.config import Network
from noxipher.core.exceptions import AddressError


def validate_address_for_network(address: str, expected_network: Network) -> bool:
    """Validate address belongs to expected network."""
    try:
        _, network, _ = decode_address(address)
        return network == expected_network
    except AddressError:
        return False


def get_address_type(address: str) -> str:
    """Get address type: 'unshielded', 'shielded', or 'dust'."""
    addr_type, _, _ = decode_address(address)
    return addr_type
