"""
ContractService — deploy and manage Compact contracts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from noxipher.contract.compact import CompactContract
from noxipher.contract.instance import ContractInstance

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
        # TODO: Full deployment flow needs transaction builder
        raise NotImplementedError("Contract deployment needs full tx builder implementation")

    def at_address(self, address: str, contract: CompactContract) -> ContractInstance:
        """Create ContractInstance for an already-deployed contract."""
        return ContractInstance(address=address, contract=contract, client=self._client)
