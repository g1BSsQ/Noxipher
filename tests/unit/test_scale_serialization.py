from noxipher.tx.scale import serialize_contract_action


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
