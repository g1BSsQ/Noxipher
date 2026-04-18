"""
Bech32m address encoding/decoding for Midnight.

Implements BIP-350 Bech32m (NOT Bech32 v0 from BIP-173).
Key difference: Bech32m uses constant 0x2bc830a3 instead of 1.

HRP table from docs.midnight.network (Apr 2026):
  Unshielded: mn_addr, mn_addr_preprod, mn_addr_preview, mn_addr_undeployed
  Shielded:   mn_shield-addr, mn_shield-addr_preprod, mn_shield-addr_preview, mn_shield-addr_undeployed
  DUST:       mn_dust, mn_dust_preprod, mn_dust_preview, mn_dust_undeployed
"""
from __future__ import annotations

from typing import Sequence

from noxipher.core.config import Network
from noxipher.core.exceptions import AddressError


# ─── Bech32m constants (BIP-350) ───
BECH32M_CONST = 0x2BC830A3
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
GENERATOR = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


def _bech32_polymod(values: list[int]) -> int:
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= GENERATOR[i] if ((top >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32m_create_checksum(hrp: str, data: list[int]) -> list[int]:
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ BECH32M_CONST
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _bech32m_verify_checksum(hrp: str, data: list[int]) -> bool:
    return _bech32_polymod(_bech32_hrp_expand(hrp) + data) == BECH32M_CONST


def _convertbits(data: bytes, frombits: int, tobits: int, pad: bool = True) -> list[int]:
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            raise AddressError(f"Invalid value in convertbits: {value}")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise AddressError("Invalid padding in convertbits")
    return ret


def bech32m_encode(hrp: str, data5: list[int]) -> str:
    """Encode HRP + 5-bit data to Bech32m string."""
    checksum = _bech32m_create_checksum(hrp, data5)
    return hrp + "1" + "".join(CHARSET[d] for d in data5 + checksum)


def bech32m_decode(bech: str) -> tuple[str, list[int]]:
    """Decode Bech32m string → (hrp, data5). Raises AddressError on failure."""
    if any(ord(x) < 33 or ord(x) > 126 for x in bech):
        raise AddressError("Invalid character in Bech32m string")
    if bech.lower() != bech and bech.upper() != bech:
        raise AddressError("Mixed case in Bech32m string")
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech):
        raise AddressError("Invalid separator position in Bech32m string")
    hrp = bech[:pos]
    data_part = bech[pos + 1 :]
    if not all(x in CHARSET for x in data_part):
        raise AddressError("Invalid character in Bech32m data part")
    data = [CHARSET.find(x) for x in data_part]
    if not _bech32m_verify_checksum(hrp, data):
        raise AddressError("Invalid Bech32m checksum")
    return hrp, data[:-6]


# ─── Midnight HRP table ───
HRP_TABLE: dict[tuple[str, Network], str] = {
    ("unshielded", Network.MAINNET): "mn_addr",
    ("unshielded", Network.PREPROD): "mn_addr_preprod",
    ("unshielded", Network.PREVIEW): "mn_addr_preview",
    ("unshielded", Network.UNDEPLOYED): "mn_addr_undeployed",
    ("shielded", Network.MAINNET): "mn_shield-addr",
    ("shielded", Network.PREPROD): "mn_shield-addr_preprod",
    ("shielded", Network.PREVIEW): "mn_shield-addr_preview",
    ("shielded", Network.UNDEPLOYED): "mn_shield-addr_undeployed",
    ("dust", Network.MAINNET): "mn_dust",
    ("dust", Network.PREPROD): "mn_dust_preprod",
    ("dust", Network.PREVIEW): "mn_dust_preview",
    ("dust", Network.UNDEPLOYED): "mn_dust_undeployed",
}

# Reverse map HRP → (type, network)
HRP_REVERSE: dict[str, tuple[str, Network]] = {v: k for k, v in HRP_TABLE.items()}


def encode_address(payload: bytes, addr_type: str, network: Network) -> str:
    """
    Encode raw bytes to Bech32m address string.

    Args:
        payload: Raw address bytes (32 bytes for unshielded/dust, 64 bytes for shielded)
        addr_type: "unshielded" | "shielded" | "dust"
        network: Target network

    Returns:
        Bech32m address string (e.g. "mn_addr_preprod1...")
    """
    hrp = HRP_TABLE.get((addr_type, network))
    if hrp is None:
        raise AddressError(f"Unknown address type/network: {addr_type}/{network}")
    data5 = _convertbits(payload, 8, 5, pad=True)
    return bech32m_encode(hrp, data5)


def decode_address(address: str) -> tuple[str, Network, bytes]:
    """
    Decode Bech32m address.

    Returns:
        (addr_type, network, payload_bytes)
    """
    hrp, data5 = bech32m_decode(address)
    info = HRP_REVERSE.get(hrp)
    if info is None:
        raise AddressError(f"Unknown HRP: {hrp}")
    payload = bytes(_convertbits(bytes(data5), 5, 8, pad=False))
    addr_type, network = info
    return addr_type, network, payload


def validate_address(address: str) -> bool:
    """Return True if address is valid Midnight Bech32m."""
    try:
        decode_address(address)
        return True
    except AddressError:
        return False
