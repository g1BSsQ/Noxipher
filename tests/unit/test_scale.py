from noxipher.tx.scale import (
    SubstrateScaleEncoder,
    serialize_string,
    serialize_transaction,
    serialize_u128,
)


def test_scale_bigint_u128() -> None:
    # Test vectors from serialize/tests/serialize.rs
    assert serialize_u128(0).hex() == "00"
    assert serialize_u128(1).hex() == "04"
    assert serialize_u128(42).hex() == "a8"
    assert serialize_u128(69).hex() == "1501"
    # 65535 = 0xFFFF
    # In Midnight ScaleBigInt:
    # occupied = 2, can_squeeze = False (0xFF >= 64)
    # size = 4
    # b0 = bot6(0xFF) | 0b10 = 0xFC | 0x02 = 0xFE
    # b1 = top2(0xFF) | bot6(0xFF) = 0x03 | 0xFC = 0xFF
    # b2 = top2(0xFF) | bot6(0x00) = 0x03 | 0x00 = 0x03
    # b3 = top2(0x00) = 0x00
    # Result: FE FF 03 00
    assert serialize_u128(65535).hex() == "feff0300"


def test_serialize_string() -> None:
    # String "test"
    # len = 4 (u64) -> 0x10 (ScaleBigInt u64)
    # UTF-8 "test" -> 74 65 73 74
    # Result: 10 74 65 73 74
    assert serialize_string("test").hex() == "1074657374"


def test_substrate_compact_u32() -> None:
    encoder = SubstrateScaleEncoder()
    assert encoder.compact_u32(0).hex() == "00"
    assert encoder.compact_u32(1).hex() == "04"
    assert encoder.compact_u32(63).hex() == "fc"
    assert encoder.compact_u32(64).hex() == "0101"  # (64 << 2) | 1 = 256 | 1 = 0x0101 LE


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
    # Check for tags
    assert b"midnight:transaction[v9]:" in encoded
    assert b"midnight:standard-transaction[v9]:" in encoded
    assert b"midnight:intent[v6]:" in encoded
    assert b"midnight:unshielded-offer[v1]:" in encoded
    assert b"midnight:unshielded-utxo-spend" in encoded
    assert b"midnight:unshielded-utxo-output[v1]:" in encoded

    # Check for pallet index 5 in the wrapped extrinsic
    from noxipher.tx.scale import MidnightTransactionSerializer

    serializer = MidnightTransactionSerializer()
    extrinsic = serializer.serialize_raw_midnight_tx(encoded)

    # Extrinsic version 0x04, Pallet 5, Call 0
    # body = [0x04, 0x05, 0x00, ...]
    # wrapped in length prefix
    assert extrinsic[1] == 0x04
    assert extrinsic[2] == 0x05
    assert extrinsic[3] == 0x00
