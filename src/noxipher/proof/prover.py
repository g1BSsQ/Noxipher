"""
ZKProver — orchestrate ZK proof generation for Midnight transactions.
"""

from typing import Any

from noxipher.core.exceptions import ProofError
from noxipher.proof.client import ProofServerClient
from noxipher.tx.models import ProvenTransaction, UnsignedTransaction


class ZKProver:
    """Orchestrate ZK proof generation via Proof Server."""

    def __init__(self, proof_client: ProofServerClient) -> None:
        self._client = proof_client

    async def prove_transaction(
        self, unsigned_tx: UnsignedTransaction | dict[str, Any]
    ) -> ProvenTransaction:
        """
        Prove all ZK circuits in a transaction.

        Returns: ProvenTransaction with proof_hexes populated.
        """
        # Convert dict to model if needed
        if isinstance(unsigned_tx, dict):
            tx = UnsignedTransaction.model_validate(unsigned_tx)
        else:
            tx = unsigned_tx

        # Verify proof server is running
        health = await self._client.health()
        if not health:
            raise ProofError("Proof Server is unreachable")

        # Collect circuits that need proving
        circuits = tx.circuits
        if not circuits:
            # No ZK proofs needed (simple NIGHT transfer or already proven)
            return ProvenTransaction(
                type=tx.type,
                guaranteed_hex=tx.guaranteed_hex,
                fallible_hexes=tx.fallible_hexes,
                proof_hexes=[],
                requires_unshielded_signature=tx.requires_unshielded_signature,
                signing_payload_hex=tx.signing_payload_hex,
            )

        proof_hexes = []
        for circuit in circuits:
            circuit_id = circuit["id"]
            proving_key = bytes.fromhex(circuit.get("proving_key_hex", ""))
            private_inputs = circuit.get("private_inputs", {})
            public_inputs = circuit.get("public_inputs", {})

            proof_bytes = await self._client.prove(
                circuit_id=circuit_id,
                proving_key=proving_key,
                private_inputs=private_inputs,
                public_inputs=public_inputs,
            )
            proof_hexes.append(proof_bytes.hex())

        return ProvenTransaction(
            type=tx.type,
            guaranteed_hex=tx.guaranteed_hex,
            fallible_hexes=tx.fallible_hexes,
            proof_hexes=proof_hexes,
            requires_unshielded_signature=tx.requires_unshielded_signature,
            signing_payload_hex=tx.signing_payload_hex,
        )
