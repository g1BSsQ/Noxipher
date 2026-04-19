from typing import Any


class ProofVerifier:
    """Verify ZK proofs."""

    async def verify(self, proof_bytes: bytes, public_inputs: dict[str, Any]) -> bool:
        """
        Verify a ZK proof.

        ⚠️ PLACEHOLDER: Needs ZK circuit verifier implementation.
        """
        raise NotImplementedError("ProofVerifier needs ZK circuit verifier implementation")
