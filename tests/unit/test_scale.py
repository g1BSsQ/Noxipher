from noxipher.tx.scale import (
    MidnightTransactionSerializer,
    serialize_transaction,
    serialize_u128,
    serialize_bytes,
)


def test_scale_u128() -> None:
    # Test vectors for LE u128
    assert serialize_u128(0).hex() == "00" * 16
    assert serialize_u128(1).hex() == "01" + "00" * 15


def test_serialize_bytes() -> None:
    # String "test" -> bytes
    # len = 4 -> 0x10 in SCALE compact
    # Result: 10 74 65 73 74
    assert serialize_bytes(b"test").hex() == "1074657374"


def test_unshielded_transaction_structure() -> None:
    # Construct a minimal unshielded transfer dict
    tx_data = {
        "standard": {
            "network_id": "test",
            "intents": {
                "0": {
                    "guaranteed_unshielded_offer": {
                        "inputs": [
                            {
                                "value": 100,
                                "owner": b"\x01" * 32,
                                "type_": 0,
                                "intent_hash": b"\x02" * 32,
                                "output_no": 0,
                            }
                        ],
                        "outputs": [{"value": 100, "owner": b"\x03" * 32, "type_": 0}],
                        "signatures": [b"\x04" * 64],
                    },
                    "ttl": 0,
                    "binding_commitment": b"\x00" * 32,
                }
            },
            "binding_randomness": b"\x00" * 32,
        }
    }

    encoded = serialize_transaction(tx_data)
    # Check for tags in new format
    assert b"standard-tx[v1]" in encoded
    assert b"unshielded-sig[v1]" not in encoded  # This is for signing payload
    
    # Check for pallet index 5 in the wrapped extrinsic
    serializer = MidnightTransactionSerializer()
    extrinsic = serializer.serialize_raw_midnight_tx(encoded)

    # Pallet 5, Call 0
    # [0x05, 0x00, length, ...]
    assert extrinsic[0] == 0x05
    assert extrinsic[1] == 0x00

