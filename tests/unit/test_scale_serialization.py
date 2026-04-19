from noxipher.tx.scale import (
    serialize_contract_action,
    serialize_contract_args,
    serialize_zswap_offer,
)


def test_serialize_contract_call() -> None:
    action = {
        "type": "call",
        "address": b"\x01" * 32,
        "entry_point": "test_method",
        "args": b"\x01\x02\x03"
    }
    encoded = serialize_contract_action(action)
    assert encoded.startswith(b"midnight:contract-action[v1]:")
    # Discriminant 1 (Call)
    payload = encoded.split(b":")[-1]
    assert payload[0] == 1
    assert payload[1:33] == b"\x01" * 32
    # entry_point: length (11) + "test_method"
    # Midnight ScaleBigInt for 11 is 11 << 2 | 0 = 44 = 0x2c
    assert payload[33] == 0x2c
    assert b"test_method" in payload

def test_serialize_contract_deploy() -> None:
    action = {
        "type": "deploy",
        "bytecode": b"\xde\xad\xbe\xef",
        "initial_state": b"\x00"
    }
    encoded = serialize_contract_action(action)
    assert encoded.startswith(b"midnight:contract-action[v1]:")
    payload = encoded.split(b":")[-1]
    # Discriminant 0 (Deploy)
    assert payload[0] == 0
    # bytecode: length (4) + bytes
    assert payload[1] == (4 << 2)
    assert b"\xde\xad\xbe\xef" in payload

def test_serialize_contract_args() -> None:
    # Int
    assert serialize_contract_args(123) == b"\xed\x01" # 123 << 2 | 1 (marker) = 493 = 0x1ed
    # String
    encoded_str = serialize_contract_args("hello")
    assert b"hello" in encoded_str
    # List
    encoded_list = serialize_contract_args([1, 2])
    assert encoded_list[0] == (2 << 2) # length 2
    # Dict
    encoded_dict = serialize_contract_args({"a": 1})
    assert encoded_dict[0] == (1 << 2) # 1 pair
    assert b"a" in encoded_dict

def test_serialize_zswap_offer_advanced() -> None:
    offer = {
        "spend_proofs": [b"\x01" * 32],
        "output_proofs": [b"\x02" * 32],
        "zswap_memos": [b"\x03" * 64],
        "merkle_root": b"\x04" * 32
    }
    encoded = serialize_zswap_offer(offer)
    assert encoded.startswith(b"midnight:zswap-offer[v1]:")
    payload = encoded.split(b":")[-1]
    assert payload[0] == 0 # Shielded discriminant
    # spends length (1) + bytes (encoded)
    assert payload[1] == (1 << 2)
    assert b"\x01" * 32 in payload
    # outputs length (1) + bytes (encoded)
    assert b"\x02" * 32 in payload
    # memos length (1) + 64 bytes
    assert b"\x03" * 64 in payload
    # root
    assert b"\x04" * 32 in payload
