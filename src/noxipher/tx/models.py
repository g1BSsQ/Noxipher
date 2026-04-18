"""
Transaction models — Pydantic models mirroring Midnight ledger structure.

Structure from midnight-ledger/ledger/src/structure.rs:
  StandardTransaction { guaranteed, segments, proofs, signature }
  Segment { offer: ZswapOffer, intent: Option<Intent> }
  Intent { contract_address, entry_point, args, outputs }

Tagged serialization tags (from Tagged impls in structure.rs):
  Transaction        → "midnight:Transaction:"
  StandardTransaction → "midnight:StandardTransaction:"
"""

from __future__ import annotations

from pydantic import BaseModel


class TransactionReceipt(BaseModel):
    """Result of a submitted transaction."""

    hash: str
    block_height: int | None = None
    block_hash: str | None = None
    status: str  # "SUCCESS", "PARTIAL_SUCCESS", "FAILURE"
    fee_paid: int = 0  # Specks


class UnshieldedInput(BaseModel):
    """Unshielded NIGHT UTxO input."""

    tx_hash: str  # Transaction hash of the UTxO being spent
    output_index: int  # Output index within the transaction


class UnshieldedOutput(BaseModel):
    """Unshielded NIGHT UTxO output."""

    recipient: str  # Midnight address (mn_addr_...)
    value: int  # Amount in Specks (1 NIGHT = 10^12 Specks)
    token_type: str = (
        "0000000000000000000000000000000000000000000000000000000000000000"  # NIGHT = 32 zero bytes
    )


class ZswapCoinNote(BaseModel):
    """Shielded coin commitment (for ZSwap offers)."""

    commitment: str  # hex-encoded 32-byte commitment
    value: int
    token_type: str
    encrypted_data: str = ""  # hex-encoded encrypted coin note


class ZswapOffer(BaseModel):
    """
    ZSwap offer — shielded coin operations.

    Mirrors ledger/src/structure.rs ZswapOffer:
      - inputs: spend nullifiers
      - outputs: new coin commitments
      - transients: temporary coins (contract-internal)
    """

    inputs: list[str] = []  # hex-encoded nullifiers
    outputs: list[ZswapCoinNote] = []
    transients: list[str] = []  # hex-encoded transient commitments
    root: str = ""  # Merkle tree root (hex)


class Intent(BaseModel):
    """
    Contract call intent — defines what a contract call does.

    Mirrors ledger/src/structure.rs Intent struct.
    """

    contract_address: str  # hex-encoded contract address
    entry_point: str  # Entry point name (e.g., "increment")
    guaranteed_offer: ZswapOffer = ZswapOffer()
    fallible_offer: ZswapOffer = ZswapOffer()


class Segment(BaseModel):
    """
    Transaction segment — one fallible execution unit.

    Mirrors ledger/src/structure.rs Segment:
      offer: ZswapOffer
      intent: Option<Intent>
    """

    offer: ZswapOffer = ZswapOffer()
    intent: Intent | None = None


class UnsignedTransaction(BaseModel):
    """
    Unsigned transaction — before ZK proof generation.

    Built by TransactionBuilder, passed to ZKProver.
    """

    type: str  # "unshielded_transfer" | "shielded_transfer" | "contract_call"

    # Guaranteed segment (always executed)
    guaranteed_offer: ZswapOffer = ZswapOffer()
    unshielded_inputs: list[UnshieldedInput] = []
    unshielded_outputs: list[UnshieldedOutput] = []

    # Fallible segments (contract calls)
    segments: list[Segment] = []

    # Signing info
    requires_unshielded_signature: bool = False
    signing_payload_hex: str = ""  # Populated after balancing

    # For internal use
    circuits: list[dict] = []  # ZK circuits needing proof
    guaranteed_hex: str = ""  # Pre-serialized guaranteed segment
    fallible_hexes: list[str] = []


class ProvenTransaction(BaseModel):
    """
    Proven transaction — after ZK proof generation by Proof Server.

    Flow from Counter CLI:
      1. finalize_recipe() → balanced tx
      2. sign('pre-proof') → signed for proving
      3. prove() → ZK proofs generated
      4. sign('proof') → signed with proofs
    """

    type: str
    guaranteed_hex: str = ""
    fallible_hexes: list[str] = []
    proof_hexes: list[str] = []
    requires_unshielded_signature: bool = False
    signing_payload_hex: str = ""
    signature_hex: str = ""  # Sr25519 signature hex
