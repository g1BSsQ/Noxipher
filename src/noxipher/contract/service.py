"""
ContractService — deploy and manage Compact contracts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from noxipher.contract.compact import CompactContract
from noxipher.contract.instance import ContractInstance
from noxipher.core.logger import get_logger

log = get_logger(__name__)

if TYPE_CHECKING:
    from noxipher.core.client import NoxipherClient
    from noxipher.wallet.wallet import MidnightWallet


class ContractService:
    """Service for deploying and interacting with Compact contracts."""

    def __init__(self, client: NoxipherClient) -> None:
        self._client = client

    def load_contract(self, circuit_dir: Path) -> CompactContract:
        """Load a compiled Compact contract from directory."""
        return CompactContract.from_directory(circuit_dir)

    async def deploy(
        self,
        contract: CompactContract,
        wallet: MidnightWallet,
        initial_state: dict[str, Any] | None = None,
    ) -> ContractInstance:
        """
        Deploy a contract to the network.

        Returns: ContractInstance with deployed address.
        """
        # For now, we assume bytecode is passed as a string/bytes in initial_state or similar
        # Real compact contracts have a .wasm circuit that acts as bytecode
        bytecode = contract.get_circuit_path(contract.name).read_bytes()

        receipt = await self._client.tx.deploy_contract(
            wallet=wallet,
            bytecode=bytecode,
            initial_state=initial_state or {},
        )

        # Address is extracted from receipt events (ContractDeployed)
        address = receipt.contract_address
        if not address:
            # Fallback for older indexers or testnets
            log.warning("contract_address_not_found_in_receipt", tx_hash=receipt.hash)
            address = f"0x{receipt.hash[:64]}"
        return self.at_address(address, contract)

    def at_address(self, address: str, contract: CompactContract) -> ContractInstance:
        """Create ContractInstance for an already-deployed contract."""
        return ContractInstance(address=address, contract=contract, client=self._client)
