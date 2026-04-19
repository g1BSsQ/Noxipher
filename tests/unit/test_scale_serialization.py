from noxipher.tx.scale import (
    serialize_contract_action,
    serialize_contract_args,
    serialize_zswap_offer,
    encode_scale_int,
)


def test_serialize_contract_call() -> None:
    action = {
        "type": "call",
        "address": b"\x01" * 32,
        "entry_point": "test_method",
        "args": b"\x01\x02\x03"
    }
    encoded = serialize_contract_action(action)
    # Discriminant 1 (Call)
    assert encoded[0] == 1
    assert encoded[1:33] == b"\x01" * 32
    # entry_point: length (11) + "test_method"
    assert encoded[33] == (11 << 2)
    assert b"test_method" in encoded


def test_serialize_contract_deploy() -> None:
    action = {
        "type": "deploy",
        "bytecode": b"\xde\xad\xbe\xef",
        "initial_state": b"\x00"
    }
    encoded = serialize_contract_action(action)
    # Discriminant 0 (Deploy)
    assert encoded[0] == 0
    # bytecode: length (4) + bytes
    assert encoded[1] == (4 << 2)
    assert b"\xde\xad\xbe\xef" in encoded


def test_serialize_contract_args() -> None:
    # Int
    # 123 < 64 -> 123 << 2 = 492 = 0x1ec ? No, 123 is >= 64
    # 123 < 16384 -> (123 << 2) | 1 = 492 | 1 = 493 = 0x01ed
    assert serialize_contract_args(123) == b"\xed\x01"
    # String
    encoded_str = serialize_contract_args("hello")
    assert b"hello" in encoded_str
    # List
    encoded_list = serialize_contract_args([1, 2])
    assert encoded_list[0] == (2 << 2) # length 2
    # Dict (Struct)
    encoded_dict = serialize_contract_args({"a": 1, "b": 2})
    # SCALE Struct: Concatenate values in order, no length, no keys
    assert encoded_dict == serialize_contract_args(1) + serialize_contract_args(2)


def test_serialize_zswap_offer_advanced() -> None:
    offer = {
        "spend_proofs": [b"\x01" * 32],
        "output_proofs": [b"\x02" * 32],
        "zswap_memos": [b"\x03" * 64],
        "merkle_root": b"\x04" * 32
    }
    encoded = serialize_zswap_offer(offer)
    # Tagged with zswap-offer[v1]
    tag = "zswap-offer[v1]"
    assert encoded.startswith(encode_scale_int(len(tag)) + tag.encode())
    
    payload = encoded[len(encode_scale_int(len(tag))) + len(tag):]
    # spends length (1) + bytes
    assert payload[0] == (1 << 2)
    assert b"\x01" * 32 in payload
    # outputs length (1) + bytes
    assert b"\x02" * 32 in payload
    # memos length (1) + 64 bytes
    assert b"\x03" * 64 in payload
    # root
    assert b"\x04" * 32 in payload

