"""
ProofServerClient — HTTP client for Midnight Proof Server.

Proof Server v8.0.3:
  docker run -p 6300:6300 midnightntwrk/proof-server:8.0.3 midnight-proof-server -v

Proof Server API:
  GET  /health                → {"status": "ok", "version": "..."}
  POST /prove                 → ZK proof bytes
  GET  /keys/{circuit_id}    → Proving key download
"""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from noxipher.core.exceptions import ProofError


class ProofServerClient:
    """
    Async HTTP client for Proof Server.

    Proof Server runs LOCAL (private data never leaves user's machine).
    Or use hosted: lace-proof-pub.<network>.midnight.network
    """

    def __init__(self, proof_server_url: str, timeout: float = 300.0) -> None:
        # ZK proof generation can take several minutes
        self._url = proof_server_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ProofServerClient:
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    async def health(self) -> dict:
        """
        GET /health → {"status": "ok", "version": "8.0.3", ...}

        Verify proof server is running and version is correct.
        """
        try:
            resp = await self._client.get(f"{self._url}/health")  # type: ignore[union-attr]
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise ProofError(f"Proof server health check failed: {e}") from e

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=30))
    async def prove(
        self,
        circuit_id: str,
        proving_key: bytes,
        private_inputs: dict,
        public_inputs: dict,
    ) -> bytes:
        """
        POST /prove → ZK proof bytes.

        ⚠️ REQUEST FORMAT NOT YET VERIFIED.
        """
        payload = {
            "circuitId": circuit_id,
            "provingKey": proving_key.hex(),
            "privateInputs": private_inputs,
            "publicInputs": public_inputs,
        }
        try:
            resp = await self._client.post(f"{self._url}/prove", json=payload)  # type: ignore[union-attr]
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPError as e:
            raise ProofError(f"Proof generation failed: {e}") from e

    async def get_proving_key(self, circuit_id: str) -> bytes:
        """GET /keys/{circuit_id} → Proving key bytes."""
        try:
            resp = await self._client.get(f"{self._url}/keys/{circuit_id}")  # type: ignore[union-attr]
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPError as e:
            raise ProofError(f"Failed to get proving key for {circuit_id}: {e}") from e
