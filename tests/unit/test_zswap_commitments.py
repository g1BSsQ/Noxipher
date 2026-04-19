
import pytest
from noxipher.zswap.notes import ShieldedCoinNote

def test_shielded_coin_commitment():
    token_type = b"\x00" * 32
    owner_pk = b"\x01" * 32
    nonce = b"\x02" * 32
    value = 1000
    
    note = ShieldedCoinNote(
        token_type=token_type,
        value=value,
        nonce=nonce,
        owner_pk=owner_pk,
        merkle_tree_index=0
    )
    
    commitment = note.compute_commitment()
    assert len(commitment) == 32
    assert commitment != b"\x00" * 32
    
    # Verify stability
    assert commitment == note.compute_commitment()
    
    # Verify change
    note2 = ShieldedCoinNote(
        token_type=token_type,
        value=value + 1,
        nonce=nonce,
        owner_pk=owner_pk,
        merkle_tree_index=0
    )
    assert commitment != note2.compute_commitment()
