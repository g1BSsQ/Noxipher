"""
SCALE encoding helpers for Midnight transaction types.

Reverse-engineered from midnight-ledger/serialize/src/util.rs.

Key insight from util.rs:
  - u32, u64, u128 use ScaleBigInt (NOT standard SCALE compact encoding)
  - ScaleBigInt has 4 modes: 1-byte, 2-byte, 4-byte, N-byte
  - Bit layout is custom (NOT the same as parity-scale-codec compact)
  - Vec<T> serializes len as u32 (via ScaleBigInt), then each element
  - Option<T>: 0u8 = None, 1u8 + value = Some

Test vectors (from serialize/tests/serialize.rs):
  ser(0u128)              = [0x00]
  ser(1u128)              = [0x04]
  ser(42u128)             = [0xa8]
  ser(69u128)             = [0x15, 0x01]
  ser(65535u128)          = [0xfe, 0xff, 0x03, 0x00]
  ser(100000000000000u128)= [0x0b, 0x00, 0x40, 0x7a, 0x10, 0xf3, 0x5a]

Tagged serialization format (from serializable.rs):
  tagged_serialize(value) = b"midnight:" + tag + b":" + serialize(value)
"""

from __future__ import annotations

from typing import Any


SCALE_MAX_BYTES = 67
SCALE_ONE_BYTE_MARKER = 0b00
SCALE_TWO_BYTE_MARKER = 0b01
SCALE_FOUR_BYTE_MARKER = 0b10
SCALE_N_BYTE_MARKER = 0b11

GLOBAL_TAG = "midnight:"


class ScaleBigInt:
    """
    Custom Midnight big-integer encoding — mirrors util.rs ScaleBigInt exactly.

    This is NOT the same as parity-scale-codec compact encoding.
    u32/u64/u128 all route through this encoding.
    """

    def __init__(self, value_bytes: bytes) -> None:
        """
        Args:
            value_bytes: little-endian bytes representation (up to 67 bytes)
        """
        if len(value_bytes) > SCALE_MAX_BYTES:
            raise ValueError(f"ScaleBigInt too large: {len(value_bytes)} > {SCALE_MAX_BYTES}")
        self._data = bytearray(SCALE_MAX_BYTES)
        self._data[: len(value_bytes)] = value_bytes

    @classmethod
    def from_int(cls, value: int, n_bytes: int) -> ScaleBigInt:
        """Create from integer with explicit byte width (4, 8, or 16)."""
        le_bytes = value.to_bytes(n_bytes, "little")
        return cls(le_bytes)

    @classmethod
    def from_u32(cls, value: int) -> ScaleBigInt:
        return cls.from_int(value, 4)

    @classmethod
    def from_u64(cls, value: int) -> ScaleBigInt:
        return cls.from_int(value, 8)

    @classmethod
    def from_u128(cls, value: int) -> ScaleBigInt:
        return cls.from_int(value, 16)

    def serialized_size(self) -> int:
        """
        Mirrors Rust serialized_size():
          - Count trailing zero bytes
          - occupied = SCALE_MAX_BYTES - trailing_zeros
          - can_squeeze = data[occupied-1] < 64
          - Match (occupied, can_squeeze) to determine encoding size
        """
        trailing_zeros = 0
        for b in reversed(self._data):
            if b == 0:
                trailing_zeros += 1
            else:
                break
        occupied = SCALE_MAX_BYTES - trailing_zeros
        can_squeeze = occupied == 0 or self._data[occupied - 1] < 64
        if occupied == 0 or (occupied == 1 and can_squeeze):
            return 1
        elif (occupied == 1 and not can_squeeze) or (occupied == 2 and can_squeeze):
            return 2
        elif (
            (occupied == 2 and not can_squeeze) or occupied == 3 or (occupied == 4 and can_squeeze)
        ):
            return 4
        else:
            return occupied + 1

    def serialize(self) -> bytes:
        """
        Mirrors Rust serialize():
          size 1: [bot6bits(data[0]) | ONE_BYTE]
          size 2: [bot6bits(data[0]) | TWO_BYTE, top2bits(data[0]) | bot6bits(data[1])]
          size 4: 4 bytes with interleaved top2/bot6 packing
          size n: [(n-5)<<2 | N_BYTE, data[0..n-1]]
        """

        def top2bits(b: int) -> int:
            return (b & 0b1100_0000) >> 6

        def bot6bits(b: int) -> int:
            return (b & 0b0011_1111) << 2

        size = self.serialized_size()
        d = self._data

        if size == 1:
            return bytes([bot6bits(d[0]) | SCALE_ONE_BYTE_MARKER])
        elif size == 2:
            b0 = bot6bits(d[0]) | SCALE_TWO_BYTE_MARKER
            b1 = top2bits(d[0]) | bot6bits(d[1])
            return bytes([b0, b1])
        elif size == 4:
            b0 = bot6bits(d[0]) | SCALE_FOUR_BYTE_MARKER
            b1 = top2bits(d[0]) | bot6bits(d[1])
            b2 = top2bits(d[1]) | bot6bits(d[2])
            b3 = top2bits(d[2]) | bot6bits(d[3])
            return bytes([b0, b1, b2, b3])
        else:
            header = ((size - 5) << 2 | SCALE_N_BYTE_MARKER) & 0xFF
            return bytes([header]) + bytes(d[: size - 1])

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple[ScaleBigInt, int]:
        """
        Decode ScaleBigInt from bytes at offset.
        Returns (ScaleBigInt, bytes_consumed).

        Mirrors Rust deserialize().
        """
        first = data[offset]
        result = cls(b"")

        def top6bits(b: int) -> int:
            return (b & 0b1111_1100) >> 2

        def bot2bits(b: int) -> int:
            return (b & 0b0000_0011) << 6

        mode = first & 0b11
        if mode == SCALE_ONE_BYTE_MARKER:
            result._data[0] = top6bits(first)
            return result, 1
        elif mode == SCALE_TWO_BYTE_MARKER:
            second = data[offset + 1]
            result._data[0] = top6bits(first) | bot2bits(second)
            result._data[1] = top6bits(second)
            return result, 2
        elif mode == SCALE_FOUR_BYTE_MARKER:
            second = data[offset + 1]
            third = data[offset + 2]
            fourth = data[offset + 3]
            result._data[0] = top6bits(first) | bot2bits(second)
            result._data[1] = top6bits(second) | bot2bits(third)
            result._data[2] = top6bits(third) | bot2bits(fourth)
            result._data[3] = top6bits(fourth)
            return result, 4
        else:  # N_BYTE_MARKER
            n = top6bits(first) + 4
            result._data[:n] = data[offset + 1 : offset + 1 + n]
            return result, n + 1

    def to_int(self) -> int:
        """Convert to Python int (little-endian)."""
        return int.from_bytes(self._data, "little")


# ─────────────────────────────────────────────────────────────────
# Convenience helpers for common types (mirrors via_scale! macro)
# ─────────────────────────────────────────────────────────────────


def serialize_u32(value: int) -> bytes:
    return ScaleBigInt.from_u32(value).serialize()


def serialize_u64(value: int) -> bytes:
    return ScaleBigInt.from_u64(value).serialize()


def serialize_u128(value: int) -> bytes:
    return ScaleBigInt.from_u128(value).serialize()


def serialize_le_u8(value: int) -> bytes:
    """u8 → little-endian (via_le_bytes! in util.rs)."""
    return bytes([value & 0xFF])


def serialize_le_u16(value: int) -> bytes:
    return value.to_bytes(2, "little")


def serialize_bytes_fixed(data: bytes) -> bytes:
    """[u8; N] → raw bytes (no length prefix)."""
    return data


def serialize_vec(items: list[bytes]) -> bytes:
    """
    Vec<T> serialization from serializable.rs:
      len as u32 (ScaleBigInt), then each element.
    Note: length encodes as ScaleBigInt u32, NOT standard SCALE compact.
    """
    result = serialize_u32(len(items))
    for item in items:
        result += item
    return result


def serialize_option(data: bytes | None) -> bytes:
    """Option<T>: 0u8 for None, 1u8 + value for Some."""
    if data is None:
        return bytes([0])
    return bytes([1]) + data


def serialize_string(s: str) -> bytes:
    """
    String/str serialization from serializable.rs:
      len as u64 (ScaleBigInt/via_le_bytes), then UTF-8 bytes.
    In Midnight, str length uses u64 serialized via ScaleBigInt.
    """
    encoded = s.encode("utf-8")
    return serialize_u64(len(encoded)) + encoded


# ─────────────────────────────────────────────────────────────────
# Tagged serialization protocol
# ─────────────────────────────────────────────────────────────────


def tagged_serialize(tag: str, payload: bytes) -> bytes:
    """
    Midnight tagged serialization format (from serializable.rs):
      b"midnight:" + tag + b":" + payload
    """
    prefix = f"{GLOBAL_TAG}{tag}:".encode("ascii")
    return prefix + payload


def tagged_deserialize(data: bytes, expected_tag: str) -> bytes:
    """
    Decode tagged data. Strips 'midnight:<tag>:' prefix.
    Returns raw payload bytes.
    """
    prefix = f"{GLOBAL_TAG}{expected_tag}:".encode("ascii")
    if not data.startswith(prefix):
        raise ValueError(f"Expected tag 'midnight:{expected_tag}:', got prefix: {data[:50]!r}")
    return data[len(prefix) :]


# ─────────────────────────────────────────────────────────────────
# Midnight Complex Types Serializers
# ─────────────────────────────────────────────────────────────────


def serialize_transaction(transaction: dict[str, Any]) -> bytes:
    """
    Transaction enum [v9].
    Discriminant 0 = StandardTransaction.
    """
    # Assuming StandardTransaction for now
    payload = bytes([0]) + serialize_standard_transaction(transaction["standard"])
    return tagged_serialize("transaction[v9]", payload)


def serialize_standard_transaction(stx: dict[str, Any]) -> bytes:
    """
    StandardTransaction [v9].
    Fields: network_id, intents, guaranteed_coins, fallible_coins, binding_randomness
    """
    payload = bytearray()
    payload += serialize_string(stx["network_id"])

    # intents: HashMap<u16, Intent> -> serialize as Vec<(u16, Intent)>
    intents = stx["intents"]
    payload += serialize_u32(len(intents))
    for k, v in intents.items():
        payload += serialize_le_u16(int(k))
        payload += serialize_intent(v)

    # guaranteed_coins: Option<Sp<ZswapOffer>>
    payload += serialize_option(stx.get("guaranteed_coins"))

    # fallible_coins: HashMap<u16, ZswapOffer>
    fallible_coins = stx.get("fallible_coins", {})
    payload += serialize_u32(len(fallible_coins))
    for k, v in fallible_coins.items():
        payload += serialize_le_u16(int(k))
        # payload += serialize_zswap_offer(v) # Not implemented yet
        payload += v

    # binding_randomness: PedersenRandomness (32 bytes)
    payload += stx.get("binding_randomness", b"\x00" * 32)

    return tagged_serialize("standard-transaction[v9]", bytes(payload))


def serialize_intent(intent: dict[str, Any]) -> bytes:
    """
    Intent [v6].
    Fields: guaranteed_unshielded_offer, fallible_unshielded_offer, actions,
    dust_actions, ttl, binding_commitment

    """
    payload = bytearray()

    # guaranteed_unshielded_offer: Option<Sp<UnshieldedOffer>>
    guo = intent.get("guaranteed_unshielded_offer")
    if guo:
        payload += bytes([1]) + serialize_unshielded_offer(guo)
    else:
        payload += bytes([0])

    # fallible_unshielded_offer: Option<Sp<UnshieldedOffer>>
    fuo = intent.get("fallible_unshielded_offer")
    if fuo:
        payload += bytes([1]) + serialize_unshielded_offer(fuo)
    else:
        payload += bytes([0])

    # actions: Array<ContractAction>
    actions = intent.get("actions", [])
    payload += serialize_u32(len(actions))
    for act in actions:
        # payload += serialize_contract_action(act) # Not implemented yet
        payload += act

    # dust_actions: Option<Sp<DustActions>>
    payload += serialize_option(intent.get("dust_actions"))

    # ttl: Timestamp (u64)
    payload += serialize_u64(intent.get("ttl", 0))

    # binding_commitment: Pedersen (Fr/32 bytes)
    payload += intent.get("binding_commitment", b"\x00" * 32)

    return tagged_serialize("intent[v6]", bytes(payload))


def serialize_unshielded_offer(offer: dict[str, Any]) -> bytes:
    """
    UnshieldedOffer [v1].
    Fields: inputs (Array<UtxoSpend>), outputs (Array<UtxoOutput>), signatures (Array<Signature>)
    """
    payload = bytearray()

    # inputs: Array<UtxoSpend>
    inputs = offer.get("inputs", [])
    payload += serialize_u32(len(inputs))
    for i in inputs:
        payload += serialize_utxo_spend(i)

    # outputs: Array<UtxoOutput>
    outputs = offer.get("outputs", [])
    payload += serialize_u32(len(outputs))
    for o in outputs:
        payload += serialize_utxo_output(o)

    # signatures: Array<Signature>
    sigs = offer.get("signatures", [])
    payload += serialize_u32(len(sigs))
    for s in sigs:
        # Each signature is 64 bytes raw
        payload += s

    return tagged_serialize("unshielded-offer[v1]", bytes(payload))


def serialize_utxo_spend(spend: dict[str, Any]) -> bytes:
    """
    UtxoSpend.
    Fields: value (u128), owner (VerifyingKey/32B), type_ (u8), intent_hash (32B), output_no (u32)
    """
    payload = bytearray()
    payload += serialize_u128(spend["value"])
    payload += spend["owner"]  # 32 bytes
    payload += bytes([spend.get("type_", 0)])  # u8, NIGHT=0
    payload += spend["intent_hash"]  # 32 bytes
    payload += serialize_u32(spend["output_no"])

    return tagged_serialize("unshielded-utxo-spend", bytes(payload))


def serialize_utxo_output(output: dict[str, Any]) -> bytes:
    """
    UtxoOutput [v1].
    Fields: value (u128), owner (UserAddress/32B), type_ (u8)
    """
    payload = bytearray()
    payload += serialize_u128(output["value"])
    payload += output["owner"]  # 32 bytes
    payload += bytes([output.get("type_", 0)])  # u8, NIGHT=0

    return tagged_serialize("unshielded-utxo-output[v1]", bytes(payload))


def serialize_intent_fields(intent: dict[str, Any]) -> bytes:
    """
    Serialize Intent fields without the 'intent[v6]' tag.
    Used for hash-intent signing and inner intent serialization.
    """
    payload = bytearray()

    # guaranteed_unshielded_offer: Option<Sp<UnshieldedOffer>>
    guo = intent.get("guaranteed_unshielded_offer")
    if guo:
        payload += bytes([1]) + serialize_unshielded_offer(guo)
    else:
        payload += bytes([0])

    # fallible_unshielded_offer: Option<Sp<UnshieldedOffer>>
    fuo = intent.get("fallible_unshielded_offer")
    if fuo:
        payload += bytes([1]) + serialize_unshielded_offer(fuo)
    else:
        payload += bytes([0])

    # actions: Array<ContractAction>
    actions = intent.get("actions", [])
    payload += serialize_u32(len(actions))
    for act in actions:
        payload += act

    # dust_actions: Option<Sp<DustActions>>
    payload += serialize_option(intent.get("dust_actions"))

    # ttl: Timestamp (u64)
    payload += serialize_u64(intent.get("ttl", 0))

    # binding_commitment: Pedersen (Fr/32 bytes)
    payload += intent.get("binding_commitment", b"\x00" * 32)

    return bytes(payload)


def get_unshielded_signing_payload(segment_id: int, intent: dict[str, Any]) -> bytes:

    """
    Generate the bytes that need to be signed by the unshielded wallet.
    Prefix: 'midnight:hash-intent:'
    """
    data = b"midnight:hash-intent:"
    data += serialize_le_u16(segment_id)
    data += serialize_intent_fields(intent)
    return data


# ─────────────────────────────────────────────────────────────────
# Standard SCALE compact encoding (for Substrate extrinsic wrapper)
# These are DIFFERENT from ScaleBigInt — used only for the outer
# Substrate extrinsic framing layer.
# ─────────────────────────────────────────────────────────────────


class SubstrateScaleEncoder:
    """
    Standard SCALE compact encoding for Substrate extrinsic outer wrapper.

    This is parity-scale-codec compatible — used ONLY for the extrinsic
    byte-length prefix that Substrate nodes expect.
    Different from Midnight's internal ScaleBigInt encoding.
    """

    @staticmethod
    def compact_u32(value: int) -> bytes:
        """Standard SCALE compact encoding for u32."""
        if value < 64:
            return bytes([value << 2])
        elif value < 16384:
            return ((value << 2) | 1).to_bytes(2, "little")
        elif value < 1073741824:
            return ((value << 2) | 2).to_bytes(4, "little")
        raise ValueError(f"Value too large for compact u32: {value}")

    @staticmethod
    def length_prefixed(data: bytes) -> bytes:
        """SCALE bytes encoding: compact-u32 length + data."""
        return SubstrateScaleEncoder.compact_u32(len(data)) + data


# ─────────────────────────────────────────────────────────────────
# Transaction Serializer
# ─────────────────────────────────────────────────────────────────


class MidnightTransactionSerializer:
    """
    Serialize Midnight transaction → raw bytes for author_submitExtrinsic.
    """

    def serialize_raw_midnight_tx(self, midnight_tx_bytes: bytes) -> bytes:
        """
        Wrap pre-serialized midnight_tx bytes (tagged Transaction) into a Substrate extrinsic.
        """
        # The midnight_tx is SCALE-encoded as Bytes (length-prefixed)
        encoded_arg = SubstrateScaleEncoder.length_prefixed(midnight_tx_bytes)

        # call: pallet_index (5) + call_index (0) + args
        call_data = bytes([0x05, 0x00]) + encoded_arg

        # extrinsic: version (0x04) + call_data
        extrinsic_body = bytes([0x04]) + call_data

        # RPC expects length-prefixed extrinsic body
        return SubstrateScaleEncoder.length_prefixed(extrinsic_body)
