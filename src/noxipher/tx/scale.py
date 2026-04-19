"""
SCALE serialization for Midnight transaction structures.

Complies with Midnight Protocol v8.1.0-rc.1.
"""

from __future__ import annotations

import struct
from typing import Any, BinaryIO

# --- Tagged Encoding Helpers ---


def tagged_serialize(tag: str, payload: bytes) -> bytes:
    """
    Serialize in Tagged<T> format: [tag_len, tag_bytes, payload].
    """
    tag_bytes = tag.encode()
    return encode_scale_int(len(tag_bytes)) + tag_bytes + payload


# --- Core SCALE Base Types ---


def encode_scale_int(val: int) -> bytes:
    """
    Encode integer in SCALE compact format.
    """
    if val < 64:
        return bytes([val << 2])
    elif val < 16384:
        return struct.pack("<H", (val << 2) | 1)
    elif val < 1073741824:
        return struct.pack("<I", (val << 2) | 2)
    else:
        # Big-integer/large mode (not used for basic indices/lengths)
        out = bytearray()
        while val > 0:
            out.append(val & 0xFF)
            val >>= 8
        return bytes([(len(out) - 4) << 2 | 3]) + out


def serialize_u32(val: int) -> bytes:
    return struct.pack("<I", val)


def serialize_u128(val: int) -> bytes:
    return struct.pack("<QQ", val & 0xFFFFFFFFFFFFFFFF, val >> 64)


def serialize_bytes(data: bytes) -> bytes:
    """Serialize bytes with compact length prefix."""
    return encode_scale_int(len(data)) + data


# --- Midnight Specific Structures ---


def serialize_utxo_spend(spend: dict[str, Any]) -> bytes:
    """
    Serialize UtxoSpend struct.
    """
    payload = bytearray()
    payload += serialize_u128(spend["value"])
    payload += spend["owner"]  # 32 bytes
    payload += bytes([spend["type_"]])
    payload += spend["intent_hash"]  # 32 bytes
    payload += serialize_u32(spend["output_no"])
    return bytes(payload)


def serialize_utxo_output(output: dict[str, Any]) -> bytes:
    """
    Serialize UtxoOutput struct.
    """
    payload = bytearray()
    payload += serialize_u128(output["value"])
    payload += output["owner"]  # 32 bytes
    payload += bytes([output["type_"]])
    return bytes(payload)


def serialize_unshielded_offer(offer: dict[str, Any]) -> bytes:
    """
    Serialize UnshieldedOffer struct.
    """
    payload = bytearray()
    # Vec<UtxoSpend>
    payload += encode_scale_int(len(offer["inputs"]))
    for spend in offer["inputs"]:
        payload += serialize_utxo_spend(spend)

    # Vec<UtxoOutput>
    payload += encode_scale_int(len(offer["outputs"]))
    for output in offer["outputs"]:
        payload += serialize_utxo_output(output)

    # Vec<Signature>
    payload += encode_scale_int(len(offer.get("signatures", [])))
    for sig in offer.get("signatures", []):
        payload += sig  # 64 bytes Ed25519

    return bytes(payload)


def serialize_contract_action(action: dict[str, Any]) -> bytes:
    """
    Serialize ContractAction enum.
    0: Deploy, 1: Call
    """
    payload = bytearray()
    if action["type"] == "deploy":
        payload.append(0)  # Discriminant
        # bytecode: Vec<u8>
        payload += encode_scale_int(len(action["bytecode"]))
        payload += action["bytecode"]
        # initial_state: Vec<u8>
        state = action.get("initial_state", b"")
        payload += encode_scale_int(len(state))
        payload += state
    else:
        payload.append(1)  # Discriminant
        # address: Address (32 bytes)
        payload += action["address"]
        # entry_point: String
        ep_bytes = action["entry_point"].encode()
        payload += encode_scale_int(len(ep_bytes))
        payload += ep_bytes
        # args: Vec<u8>
        args_bytes = action.get("args", b"")
        payload += encode_scale_int(len(args_bytes))
        payload += args_bytes

    return bytes(payload)


def serialize_intent(intent: dict[str, Any]) -> bytes:
    """
    Serialize Intent struct.
    """
    payload = bytearray()

    # guaranteed_unshielded_offer: Option<UnshieldedOffer>
    g_offer = intent.get("guaranteed_unshielded_offer")
    if g_offer:
        payload.append(1)  # Some
        payload += serialize_unshielded_offer(g_offer)
    else:
        payload.append(0)  # None

    # fallible_unshielded_offer: Option<UnshieldedOffer>
    f_offer = intent.get("fallible_unshielded_offer")
    if f_offer:
        payload.append(1)
        payload += serialize_unshielded_offer(f_offer)
    else:
        payload.append(0)

    # ttl: u32
    payload += serialize_u32(intent["ttl"])

    # actions: Vec<ContractAction>
    actions = intent.get("actions", [])
    payload += encode_scale_int(len(actions))
    for action in actions:
        payload += serialize_contract_action(action)

    # binding_commitment: JubJubPoint (32 bytes)
    payload += intent["binding_commitment"]

    return bytes(payload)


def serialize_zswap_offer(offer: dict[str, Any]) -> bytes:
    """
    Serialize ZswapOffer struct.
    """
    payload = bytearray()

    # spend_proofs: Vec<ZswapSpendProof> (ZK Proofs are 192 bytes or similar)
    payload += encode_scale_int(len(offer["spend_proofs"]))
    for proof in offer["spend_proofs"]:
        payload += proof

    # output_proofs: Vec<ZswapOutputProof>
    payload += encode_scale_int(len(offer["output_proofs"]))
    for proof in offer["output_proofs"]:
        payload += proof

    # zswap_memos: Vec<ZswapMemo>
    payload += encode_scale_int(len(offer.get("zswap_memos", [])))
    for memo in offer.get("zswap_memos", []):
        payload += memo

    # merkle_root: MerkleRoot (32 bytes)
    root = offer.get("merkle_root", b"\x00" * 32)
    if isinstance(root, str):
        root = bytes.fromhex(root)
    payload += root[:32].ljust(32, b"\x00")

    return tagged_serialize("zswap-offer[v1]", bytes(payload))


def serialize_contract_args(args: object) -> bytes:
    """
    Serialize contract arguments using Midnight's Compact-compatible format.
    Handles basic types and nested structures.
    """
    if args is None:
        return b""
    if isinstance(args, bytes):
        return serialize_bytes(args)
    if isinstance(args, str):
        return serialize_bytes(args.encode())
    if isinstance(args, bool):
        return b"\x01" if args else b"\x00"
    if isinstance(args, int):
        return encode_scale_int(args)
    if isinstance(args, list):
        # Vec<T> format: length + serialized items
        buf = bytearray(encode_scale_int(len(args)))
        for item in args:
            buf.extend(serialize_contract_args(item))
        return bytes(buf)
    if isinstance(args, dict):
        # SCALE Struct: Concatenate values in order without length or keys
        buf = bytearray()
        for v in args.values():
            buf.extend(serialize_contract_args(v))
        return bytes(buf)
    return b""


def serialize_standard_transaction(stx: dict[str, Any]) -> bytes:
    """
    Serialize StandardTransaction struct.
    """
    payload = bytearray()

    # network_id: String
    net_bytes = stx["network_id"].encode()
    payload += encode_scale_int(len(net_bytes))
    payload += net_bytes

    # intents: BTreeMap<SegmentId, Intent>
    # SegmentId is u32
    intents = stx["intents"]
    payload += encode_scale_int(len(intents))
    # Sorted by key
    for seg_id_str in sorted(intents.keys(), key=int):
        payload += serialize_u32(int(seg_id_str))
        payload += serialize_intent(intents[seg_id_str])

    # fallible_coins: BTreeMap<SegmentId, ZswapOffer>
    f_coins = stx.get("fallible_coins", {})
    payload += encode_scale_int(len(f_coins))
    for seg_id_str in sorted(f_coins.keys(), key=int):
        payload += serialize_u32(int(seg_id_str))
        payload += serialize_zswap_offer(f_coins[seg_id_str])

    # binding_randomness: [u8; 32]
    payload += stx["binding_randomness"]

    return tagged_serialize("standard-tx[v1]", bytes(payload))


def serialize_transaction(tx_data: dict[str, Any]) -> bytes:
    """
    Main entry point for transaction serialization.
    Currently only supports StandardTransaction wrapper.
    """
    return serialize_standard_transaction(tx_data["standard"])


def get_unshielded_signing_payload(segment_id: int, intent: dict[str, Any]) -> bytes:
    """
    Payload to sign for UnshieldedOffer.
    Construction: b"midnight:unshielded-sig[v1]" || segment_id (u32) || intent_bytes
    """
    payload = bytearray(b"midnight:unshielded-sig[v1]")
    payload += serialize_u32(segment_id)
    payload += serialize_intent(intent)
    return bytes(payload)


class MidnightTransactionSerializer:
    """Wraps Midnight bytes into Substrate extrinsic payload."""

    def serialize_raw_midnight_tx(self, midnight_bytes: bytes) -> bytes:
        """
        Wraps standard-tx[v1] bytes into pallet Call.
        Pallet 5, Call 0 (submit_transaction)
        """
        # [pallet_idx, call_idx, midnight_bytes_with_len]
        payload = bytearray([5, 0])
        payload += encode_scale_int(len(midnight_bytes))
        payload += midnight_bytes
        return bytes(payload)
