"""
NodeClient — Substrate RPC client for Midnight node.

Midnight is a Substrate-based chain → substrate-interface works.
Custom Midnight types require raw RPC calls.

Standard Substrate RPC methods:
  - author_submitExtrinsic(hex_tx) → tx_hash
  - system_chain() → chain_name
  - chain_getBlockHash(height) → block_hash
  - chain_getBlock(hash) → block
  - chain_getFinalizedHead() → hash
  - chain_getHeader(hash) → header
  - state_getRuntimeVersion() → version_info

Midnight custom RPC methods (from pallets/midnight/rpc/src/lib.rs):
  - midnight_contractState(address, at?)  → hex-encoded contract state
  - midnight_zswapStateRoot(at?)          → ZSwap Merkle tree root bytes
  - midnight_ledgerStateRoot(at?)         → Ledger Merkle tree root bytes
  - midnight_ledgerVersion(at?)           → Ledger version string
  - midnight_apiVersions()                → [2] (API version array)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

try:
    from substrateinterface import SubstrateInterface
    from substrateinterface.exceptions import SubstrateRequestException

    SUBSTRATE_AVAILABLE = True
except ImportError:
    SUBSTRATE_AVAILABLE = False

from noxipher.core.config import NetworkConfig
from noxipher.core.exceptions import ConnectionError, TransactionError

logger = logging.getLogger(__name__)


class NodeClient:
    """
    Substrate RPC client for Midnight node.

    NOTE: substrate-interface is SYNCHRONOUS. Wrapped with asyncio.to_thread()
    to avoid blocking the event loop.
    """

    def __init__(self, config: NetworkConfig) -> None:
        self._ws_url = str(config.node_ws_url)
        self._substrate: Any = None  # SubstrateInterface | None

    async def connect(self) -> None:
        """Connect to Midnight node via WebSocket."""
        if not SUBSTRATE_AVAILABLE:
            raise ConnectionError(
                "substrate-interface not installed. Install with: pip install noxipher[node]"
            )
        try:
            self._substrate = await asyncio.to_thread(
                SubstrateInterface,
                url=self._ws_url,
            )
            logger.info(f"Connected to Midnight node: {self._ws_url}")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to node {self._ws_url}: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Midnight node."""
        if self._substrate:
            try:
                await asyncio.to_thread(self._substrate.close)
            except Exception:
                pass
            self._substrate = None

    async def __aenter__(self) -> NodeClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()

    def _require_connection(self) -> None:
        if not self._substrate:
            raise ConnectionError("Not connected. Call connect() first.")

    # ─────────────────────────────────────────────────────────────
    # Standard Substrate RPC methods
    # ─────────────────────────────────────────────────────────────

    async def get_health(self) -> dict[str, Any] | None:
        """Get node health (chain name). Returns None if unreachable."""
        try:
            name = await self.get_chain_name()
            return {"chain": name, "status": "ok"}
        except Exception:
            return None

    async def get_chain_name(self) -> str:
        """Verify connected to correct chain (e.g., 'Midnight Devnet')."""
        self._require_connection()
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "system_chain",
            [],
        )
        return str(result.get("result", ""))

    async def get_runtime_version(self) -> dict[str, Any]:
        """Get runtime version info including spec_version."""
        self._require_connection()
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "state_getRuntimeVersion",
            [],
        )
        return dict(result.get("result", {}))

    async def get_block_hash(self, height: int | None = None) -> str:
        """Get block hash at height. None = latest finalized block."""
        self._require_connection()
        params = [height] if height is not None else []
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "chain_getBlockHash",
            params,
        )
        return str(result.get("result", ""))

    async def get_block(self, block_hash: str | None = None) -> dict[str, Any]:
        """Get full block by hash. None = latest."""
        self._require_connection()
        params = [block_hash] if block_hash else []
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "chain_getBlock",
            params,
        )
        return dict(result.get("result", {}))

    async def get_finalized_head(self) -> str:
        """Get the hash of the latest finalized block."""
        self._require_connection()
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "chain_getFinalizedHead",
            [],
        )
        return str(result.get("result", ""))

    async def get_header(self, block_hash: str | None = None) -> dict[str, Any]:
        """Get block header."""
        self._require_connection()
        params = [block_hash] if block_hash else []
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "chain_getHeader",
            params,
        )
        return dict(result.get("result", {}))

    async def submit_extrinsic(self, raw_tx_bytes: bytes) -> str:
        """
        Submit raw transaction bytes via author_submitExtrinsic.

        Returns: tx hash (hex string)

        NOTE: Uses raw RPC, not substrate-interface extrinsic builder
        because Midnight transaction format differs from standard Substrate.

        The node runs ValidateUnsigned → send_mn_transaction dispatch.
        """
        self._require_connection()
        hex_tx = "0x" + raw_tx_bytes.hex()
        logger.debug(f"Submitting extrinsic: {len(raw_tx_bytes)} bytes")
        try:
            result = await asyncio.to_thread(
                self._substrate.rpc_request,
                "author_submitExtrinsic",
                [hex_tx],
            )
        except SubstrateRequestException as e:
            raise TransactionError(f"submit_extrinsic failed: {e}") from e

        if "error" in result:
            raise TransactionError(f"Node rejected tx: {result['error']}")
        tx_hash = str(result.get("result", ""))
        logger.info(f"Transaction submitted: {tx_hash}")
        return tx_hash

    async def submit_and_watch(self, raw_tx_bytes: bytes) -> str:
        """
        Submit transaction and subscribe to status updates.
        Returns tx hash immediately; watch events via substrate events.
        """
        self._require_connection()
        hex_tx = "0x" + raw_tx_bytes.hex()
        try:
            result = await asyncio.to_thread(
                self._substrate.rpc_request,
                "author_submitAndWatchExtrinsic",
                [hex_tx],
            )
        except SubstrateRequestException as e:
            raise TransactionError(f"submit_and_watch failed: {e}") from e

        if "error" in result:
            raise TransactionError(f"Node rejected tx: {result['error']}")
        return str(result.get("result", ""))

    # ─────────────────────────────────────────────────────────────
    # Midnight custom RPC methods
    # ─────────────────────────────────────────────────────────────

    async def get_ledger_version(self, block_hash: str | None = None) -> str:
        """
        Get Midnight ledger version string.

        RPC: midnight_ledgerVersion(at?) → String
        From pallets/midnight/rpc/src/lib.rs: get_ledger_version()
        """
        self._require_connection()
        params = [block_hash] if block_hash else [None]
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "midnight_ledgerVersion",
            params,
        )
        return str(result.get("result", ""))

    async def get_api_versions(self) -> list[int]:
        """
        Get supported Midnight RPC API versions.

        RPC: midnight_apiVersions() → [2]
        From pallets/midnight/rpc/src/lib.rs: get_supported_api_versions()
        """
        self._require_connection()
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "midnight_apiVersions",
            [],
        )
        return list(result.get("result", []))

    async def get_contract_state(
        self, contract_address_hex: str, block_hash: str | None = None
    ) -> str:
        """
        Get serialized contract state for a deployed contract.

        RPC: midnight_contractState(address, at?) → hex string
        From pallets/midnight/rpc/src/lib.rs: get_state()

        Args:
            contract_address_hex: hex-encoded contract address
            block_hash: optional block hash to query at

        Returns: hex-encoded tagged-serialized ContractState bytes
        """
        self._require_connection()
        params = [contract_address_hex, block_hash if block_hash else None]
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "midnight_contractState",
            params,
        )
        return str(result.get("result", ""))

    async def get_contract_state_bytes(
        self, contract_address_hex: str, block_hash: str | None = None
    ) -> bytes:
        """get_contract_state() returning raw bytes."""
        raw = await self.get_contract_state(contract_address_hex, block_hash)
        if isinstance(raw, str) and raw.startswith("0x"):
            return bytes.fromhex(raw[2:])
        return bytes.fromhex(raw) if raw else b""

    async def get_zswap_state_root(self, block_hash: str | None = None) -> bytes:
        """
        Get Merkle root of the ZSwap (shielded) state tree.

        RPC: midnight_zswapStateRoot(at?) → Vec<u8>
        From pallets/midnight/rpc/src/lib.rs: get_zswap_state_root()
        """
        self._require_connection()
        params = [block_hash if block_hash else None]
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "midnight_zswapStateRoot",
            params,
        )
        raw = result.get("result", "")
        if isinstance(raw, str) and raw.startswith("0x"):
            return bytes.fromhex(raw[2:])
        return b""

    async def get_ledger_state_root(self, block_hash: str | None = None) -> bytes:
        """
        Get Merkle root of the overall ledger state.

        RPC: midnight_ledgerStateRoot(at?) → Vec<u8>
        From pallets/midnight/rpc/src/lib.rs: get_ledger_state_root()
        """
        self._require_connection()
        params = [block_hash if block_hash else None]
        result = await asyncio.to_thread(
            self._substrate.rpc_request,
            "midnight_ledgerStateRoot",
            params,
        )
        raw = result.get("result", "")
        if isinstance(raw, str) and raw.startswith("0x"):
            return bytes.fromhex(raw[2:])
        return b""

    # ─────────────────────────────────────────────────────────────
    # Metadata helpers
    # ─────────────────────────────────────────────────────────────

    async def get_metadata_types(self) -> list[str]:
        """Dump Midnight runtime type registry for debugging."""
        self._require_connection()
        types = await asyncio.to_thread(self._substrate.get_metadata_types)
        return [str(t) for t in types]

    async def get_pallet_call_index(self, pallet_name: str, call_name: str) -> tuple[int, int]:
        """
        Get the call index for a pallet call from runtime metadata.

        Returns: (pallet_index, call_index) tuple
        Useful for verifying send_mn_transaction call indices.
        """
        self._require_connection()
        try:
            metadata = await asyncio.to_thread(self._substrate.get_metadata)
            for pallet in metadata.value["pallets"]:
                if pallet["name"] == pallet_name:
                    pallet_idx = pallet["index"]
                    if pallet.get("calls"):
                        for call in pallet["calls"]["calls"]:
                            if call["name"] == call_name:
                                return pallet_idx, int(call["index"])
            raise ValueError(f"Cannot find {pallet_name}.{call_name} in metadata")
        except Exception as e:
            raise ConnectionError(f"Failed to get pallet call index: {e}") from e
