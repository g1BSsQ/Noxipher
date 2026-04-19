import pytest
from noxipher.zswap.state import MerkleTree
from noxipher.crypto.fields import Fr
from noxipher.crypto.poseidon import transient_hash

def test_merkle_tree_empty_root():
    tree = MerkleTree(depth=3)
    # Root of empty tree should be precomputed zero node at depth 3
    root = tree.root()
    assert len(root) == 32
    
    # Manually compute zero root for depth 3
    z0 = b"\x00" * 32
    z1 = transient_hash([Fr.from_le_bytes(z0), Fr.from_le_bytes(z0)]).to_bytes()
    z2 = transient_hash([Fr.from_le_bytes(z1), Fr.from_le_bytes(z1)]).to_bytes()
    z3 = transient_hash([Fr.from_le_bytes(z2), Fr.from_le_bytes(z2)]).to_bytes()
    
    assert root == z3

def test_merkle_tree_single_leaf():
    tree = MerkleTree(depth=3)
    leaf = b"\x01" + b"\x00" * 31
    tree.insert(0, leaf)
    root = tree.root()
    
    # Manually compute root
    # Level 0: [leaf, z0]
    z0 = b"\x00" * 32
    l1 = transient_hash([Fr.from_le_bytes(leaf), Fr.from_le_bytes(z0)]).to_bytes()
    # Level 1: [l1, z1]
    z1 = transient_hash([Fr.from_le_bytes(z0), Fr.from_le_bytes(z0)]).to_bytes()
    l2 = transient_hash([Fr.from_le_bytes(l1), Fr.from_le_bytes(z1)]).to_bytes()
    # Level 2: [l2, z2]
    z2 = transient_hash([Fr.from_le_bytes(z1), Fr.from_le_bytes(z1)]).to_bytes()
    l3 = transient_hash([Fr.from_le_bytes(l2), Fr.from_le_bytes(z2)]).to_bytes()
    
    assert root == l3

def test_merkle_tree_proof():
    tree = MerkleTree(depth=3)
    leaf0 = b"\x01" + b"\x00" * 31
    leaf1 = b"\x02" + b"\x00" * 31
    tree.insert(0, leaf0)
    tree.insert(1, leaf1)
    
    proof = tree.proof(0)
    assert len(proof) == 3
    
    # Verify proof for leaf 0
    # Sibling 0: leaf 1
    # Sibling 1: z1
    # Sibling 2: z2
    assert proof[0] == leaf1
    z0 = b"\x00" * 32
    z1 = transient_hash([Fr.from_le_bytes(z0), Fr.from_le_bytes(z0)]).to_bytes()
    z2 = transient_hash([Fr.from_le_bytes(z1), Fr.from_le_bytes(z1)]).to_bytes()
    assert proof[1] == z1
    assert proof[2] == z2
