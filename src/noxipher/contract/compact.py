"""
Compact smart contract interface.

Compact language:
  - TypeScript-like syntax
  - Compiled by `compact compile` → ZK circuits + ABI JSON
  - compactc examples/counter/counter.compact --output-dir /tmp/out
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from noxipher.core.exceptions import ContractError


class ContractEntryPoint(BaseModel):
    """Contract entry point (function)."""

    name: str
    is_impure: bool = False  # Impure = modifies state
    param_types: list[str] = []
    return_type: str | None = None


class ContractABI(BaseModel):
    """
    Compact contract ABI — parsed from <contract>.contract.json.

    ⚠️ Schema needs verification from compactc output.
    """

    name: str
    version: str | None = None
    circuits: list[dict[str, Any]] = []

    entry_points: list[ContractEntryPoint] = []

    @classmethod
    def from_json_file(cls, path: Path) -> ContractABI:
        """Load ABI from compactc output JSON file."""
        try:
            raw = json.loads(path.read_text())
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ContractError(f"Cannot load ABI from {path}: {e}") from e

        # Parse entry points
        entry_points = []
        for ep in raw.get("entryPoints", raw.get("entry_points", [])):
            entry_points.append(
                ContractEntryPoint(
                    name=ep.get("name", ""),
                    is_impure=ep.get("impure", ep.get("is_impure", False)),
                    param_types=ep.get("params", ep.get("param_types", [])),
                    return_type=ep.get("returns", ep.get("return_type")),
                )
            )

        return cls(
            name=raw.get("name", ""),
            version=raw.get("version"),
            circuits=raw.get("circuits", []),
            entry_points=entry_points,
        )


class CompactContract:
    """
    Compiled Compact contract ready for deployment/interaction.
    Wraps contract ABI + ZK circuit files.
    """

    def __init__(self, abi: ContractABI, circuit_dir: Path) -> None:
        self._abi = abi
        self._circuit_dir = circuit_dir

    @classmethod
    def from_directory(cls, circuit_dir: Path) -> CompactContract:
        """
        Load contract from compactc output directory.

        Expected files:
          <circuit_dir>/<name>.contract.json  (ABI)
          <circuit_dir>/*.zkey                (proving keys)
          <circuit_dir>/*.wasm               (WASM circuits)
        """
        json_files = list(circuit_dir.glob("*.contract.json"))
        if not json_files:
            raise ContractError(f"No .contract.json found in {circuit_dir}")
        abi = ContractABI.from_json_file(json_files[0])
        return cls(abi=abi, circuit_dir=circuit_dir)

    @property
    def abi(self) -> ContractABI:
        """Contract ABI."""
        return self._abi

    @property
    def name(self) -> str:
        """Contract name."""
        return self._abi.name

    def get_circuit_path(self, circuit_id: str) -> Path:
        """Get path to circuit file."""
        for ext in [".wasm", ".zkey", ".params"]:
            p = self._circuit_dir / f"{circuit_id}{ext}"
            if p.exists():
                return p
        raise ContractError(f"Circuit file not found for: {circuit_id}")
