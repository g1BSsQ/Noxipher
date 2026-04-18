import hashlib


class PersistentHashWriter:
    """
    A SHA-256 based hasher.
    Matches Midnight's PersistentHashWriter in base-crypto.
    """
    def __init__(self) -> None:
        self.hasher = hashlib.sha256()

    def update(self, data: bytes) -> None:
        self.hasher.update(data)

    def finalize(self) -> bytes:
        return self.hasher.digest()

def persistent_hash(data: bytes) -> bytes:
    """One-off SHA-256 hash."""
    writer = PersistentHashWriter()
    writer.update(data)
    return writer.finalize()

def sample_bytes(length: int, domain_separator: bytes, seed: bytes) -> bytes:
    """
    Two-level hash expansion logic used for key derivation (ESK, DSK).
    Matches Midnight's sample_bytes implementation in ledger/src/dust.rs.
    Construction: hash(domain || hash(round_u64_le || seed))
    """
    result = bytearray()
    round_idx = 0
    while len(result) < length:
        # Inner hash: hash(round_u64_le || seed)
        inner = hashlib.sha256()
        inner.update(round_idx.to_bytes(8, "little"))
        inner.update(seed)
        inner_hash = inner.digest()

        # Outer hash: hash(domain || inner_hash)
        outer = PersistentHashWriter()
        outer.update(domain_separator)
        outer.update(inner_hash)
        round_hash = outer.finalize()

        bytes_to_add = min(32, length - len(result))
        result.extend(round_hash[:bytes_to_add])
        round_idx += 1
    
    return bytes(result)

def blake2_256(data: bytes) -> bytes:
    """Blake2b 256-bit hash."""
    return hashlib.blake2b(data, digest_size=32).digest()

def sha256(data: bytes) -> bytes:
    """SHA-256 hash."""
    return hashlib.sha256(data).digest()

def ripemd160(data: bytes) -> bytes:
    """RIPEMD-160 hash."""
    h = hashlib.new("ripemd160")
    h.update(data)
    return h.digest()
