"""
ContractInstance — deployed contract interaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from noxipher.contract.compact import CompactContract
from noxipher.core.exceptions import ContractError

if TYPE_CHECKING:
    from noxipher.core.client import NoxipherClient
    from noxipher.wallet.wallet import MidnightWallet


class ContractInstance:
    """
    Deployed contract on Midnight network.
    Allows calling contract entry points.
    """

    def __init__(
        self,
        address: str,
        contract: CompactContract,
        client: NoxipherClient,
    ) -> None:
        self._address = address
        self._contract = contract
        self._client = client

    @property
    def address(self) -> str:
        """Contract address."""
        return self._address

    async def call(
        self,
        entry_point: str,
        args: dict[str, Any] | None = None,
        wallet: MidnightWallet | None = None,
    ) -> dict[str, Any]:
        """
        Call contract entry point.

        Impure calls → create transaction (requires wallet).
        Pure calls → query state (no wallet needed).
        """
        ep = next(
            (e for e in self._contract.abi.entry_points if e.name == entry_point),
            None,
        )
        if ep is None:
            raise ContractError(f"Entry point not found: {entry_point}")

        if ep.is_impure:
            if wallet is None:
                raise ContractError(f"Impure entry point '{entry_point}' requires wallet")
            return await self._call_impure(entry_point, args or {}, wallet)
        else:
            return await self._call_pure(entry_point, args or {})

    async def _call_pure(self, entry_point: str, args: dict[str, Any]) -> dict[str, Any]:
        """Query contract state (no transaction)."""
        state = await self._client.indexer.get_transactions(address=self._address, limit=1)
        return {"result": state, "tx_hash": None}

    async def _call_impure(
        self, entry_point: str, args: dict[str, Any], wallet: MidnightWallet
    ) -> dict[str, Any]:
        """Call impure entry point → transaction."""
        tx_receipt = await self._client.tx.call_contract(
            wallet=wallet,
            contract_address=self._address,
            entry_point=entry_point,
            args=args,
        )
        return {"result": None, "tx_hash": tx_receipt.hash}
