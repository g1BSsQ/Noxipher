"""
Ledger models — mapping from @midnight-ntwrk/ledger-v8 TypeScript types.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ZswapOffer(BaseModel):
    """
    ZSwap offer — guaranteed or fallible segment.

    From ledger-v8:
      ZswapOffer {
        inputs: ZswapInput[],
        outputs: ZswapOutput[],
        commitments: bytes[],
        nullifiers: bytes[],
      }
    """

    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []

    commitments: list[str] = []  # hex-encoded
    nullifiers: list[str] = []  # hex-encoded


class ZswapInput(BaseModel):
    """Spend a shielded coin."""

    coin_info: dict[str, Any]

    merkle_path: list[str]


class ZswapOutput(BaseModel):
    """Create a shielded coin."""

    coin_commitment: str  # hex-encoded 32 bytes
    value: int
    token_type: str  # hex-encoded 32 bytes
    encrypted_coin: str  # hex-encoded encrypted note


class UnshieldedInput(BaseModel):
    """NIGHT UTxO being spent."""

    utxo_id: str
    value: int
    token_type: str


class UnshieldedOutput(BaseModel):
    """NIGHT UTxO being created."""

    address: str  # bech32m
    value: int
    token_type: str


class Intent(BaseModel):
    """
    Contract call intent — fallible segment.

    Intent {
      contract_address: ContractAddress,
      entry_point: string,
      guaranteed_offer: ZswapOffer,
      fallible_offer: ZswapOffer,
    }
    """

    contract_address: str
    entry_point: str
    guaranteed_offer: ZswapOffer = ZswapOffer()
    fallible_offer: ZswapOffer = ZswapOffer()


class LedgerParameters(BaseModel):
    """
    LedgerParameters — cost model and parameters.

    From official source:
      ledger.LedgerParameters.initialParameters().dust
    """

    dust_cost: int = 300_000_000_000_000  # Specks
    max_tx_gas: int | None = None
