"""
TransactionBuilder — Build, prove, serialize, sign, submit Midnight transactions.

Flow (CONFIRMED from Counter CLI source, Apr 2026):
  1. Build UnsignedTransaction
  2. Balance: wallet.finalizeRecipe(recipe)
  3. Sign unproven: signTransactionIntents(tx, signFn, 'pre-proof')
  4. Prove: ZKProver.prove_transaction() → ProofServer HTTP
  5. Sign proven: signTransactionIntents(proven_tx, signFn, 'proof')
  6. Submit: NodeClient.submit_extrinsic()
  7. Wait: IndexerClient.get_transactions(hash=tx_hash)
"""

import asyncio
from typing import TYPE_CHECKING

from noxipher.core.exceptions import TransactionError, TransactionTimeoutError

if TYPE_CHECKING:
    from noxipher.core.client import NoxipherClient
    from noxipher.tx.models import TransactionReceipt
    from noxipher.wallet.wallet import MidnightWallet


class TransactionBuilder:
    """Build and submit Midnight transactions. Pure Python."""

    def __init__(self, client: "NoxipherClient") -> None:
        self._client = client

    async def transfer(
        self,
        wallet: "MidnightWallet",
        to: str,
        amount: int,
        shielded: bool = False,
        fee: int | None = None,
    ) -> "TransactionReceipt":
        """
        Transfer NIGHT tokens.
        """
        if shielded:
            unsigned_tx = await self._build_shielded_transfer(wallet, to, amount)
            proven_tx = await self._prove_transaction(unsigned_tx)
        else:
            # Unshielded transfers are direct and don't require the Proof Server
            proven_tx = await self._build_unshielded_transfer(wallet, to, amount)

        raw_bytes = self._serialize_transaction(proven_tx, wallet)
        tx_hash = await self._client.node.submit_extrinsic(raw_bytes)
        return await self._wait_for_receipt(tx_hash)

    async def call_contract(
        self,
        wallet: "MidnightWallet",
        contract_address: str,
        entry_point: str,
        args: dict,
    ) -> "TransactionReceipt":
        """Call a contract entry point."""
        unsigned_tx = {
            "type": "contract_call",
            "contract_address": contract_address,
            "entry_point": entry_point,
            "args": args,
            "circuits": [],
            "requires_unshielded_signature": True,
        }
        proven_tx = await self._prove_transaction(unsigned_tx)
        raw_bytes = self._serialize_transaction(proven_tx, wallet)
        tx_hash = await self._client.node.submit_extrinsic(raw_bytes)
        return await self._wait_for_receipt(tx_hash)

    async def _build_unshielded_transfer(
        self, wallet: "MidnightWallet", to_address: str, amount: int
    ) -> dict:
        """
        Build unsigned unshielded transfer with UTXO selection.
        """
        from noxipher.address.bech32m import decode_address

        # 1. Decode recipient address to get 32-byte public key/address
        try:
            recipient_bytes = decode_address(to_address)
        except Exception as e:
            raise TransactionError(f"Invalid recipient address: {e}") from e

        # 2. Fetch and select UTXOs
        utxos = await wallet.unshielded.get_utxos(self._client.indexer)
        selected = []
        current_total = 0
        for utxo in utxos:
            # Only use NIGHT tokens (all zeros)
            token_type = utxo.get("token_type", "00" * 32)
            if isinstance(token_type, dict):
                token_type = token_type.get("hex", "00" * 32)

            if token_type == "00" * 32:
                selected.append(utxo)
                current_total += int(utxo.get("value", 0))
                if current_total >= amount:
                    break

        if current_total < amount:
            raise TransactionError(f"Insufficient unshielded balance: {current_total} < {amount}")

        # 3. Create Inputs (UtxoSpend)
        inputs = []
        for utxo in selected:
            # Handle both camelCase from GQL and potential snake_case mapping
            i_hash = utxo.get("intentHash") or utxo.get("intent_hash") or ("00" * 32)
            o_no = utxo.get("outputNo") or utxo.get("output_no") or 0

            inputs.append(
                {
                    "value": int(utxo["value"]),
                    "owner": wallet.unshielded.public_key,
                    "type_": 0,
                    "intent_hash": bytes.fromhex(i_hash),
                    "output_no": int(o_no),
                }
            )

        # 4. Create Outputs (UtxoOutput)
        outputs = []
        # Recipient output
        outputs.append({"value": amount, "owner": recipient_bytes, "type_": 0})
        # Change output
        if current_total > amount:
            outputs.append(
                {
                    "value": current_total - amount,
                    "owner": wallet.unshielded.public_key,
                    "type_": 0,
                }
            )

        # 5. Structure for SCALE serialization
        # This dict matches the expected input of serialize_transaction in scale.py
        unshielded_offer = {
            "inputs": inputs,
            "outputs": outputs,
            "signatures": [],  # Will be filled by signer
        }

        intent = {
            "guaranteed_unshielded_offer": unshielded_offer,
            "ttl": 0,  # No TTL for now
            "actions": [],
            "binding_commitment": b"\x00" * 32,
        }

        # The StandardTransaction envelope
        stx = {
            "network_id": self._client.config.name,
            "intents": {"0": intent},
            "binding_randomness": b"\x00" * 32,
        }

        return {
            "type": "unshielded_transfer",
            "standard": stx,
            "requires_unshielded_signature": True,
            "is_unshielded_only": True,
        }

    async def _build_shielded_transfer(
        self, wallet: "MidnightWallet", to: str, amount: int
    ) -> dict:
        """Build unsigned shielded transfer."""
        return {
            "type": "shielded_transfer",
            "from": wallet.shielded.address,
            "to": to,
            "amount": amount,
            "circuits": [],
            "requires_unshielded_signature": False,
            "guaranteed_hex": "",
            "fallible_hexes": [],
        }

    async def _prove_transaction(self, tx: dict) -> dict:
        """Prove all segments via Proof Server HTTP API."""
        from noxipher.proof.prover import ZKProver

        prover = ZKProver(self._client.proof)
        return await prover.prove_transaction(tx)

    def _serialize_transaction(self, tx_data: dict, wallet: "MidnightWallet") -> bytes:
        """Serialize transaction to raw bytes with signing."""
        from noxipher.tx.scale import (
            MidnightTransactionSerializer,
            get_unshielded_signing_payload,
            serialize_transaction,
        )

        # 1. Handle unshielded signing if needed
        if tx_data.get("requires_unshielded_signature"):
            stx = tx_data["standard"]
            for seg_id_str, intent in stx["intents"].items():
                seg_id = int(seg_id_str)
                # Sign guaranteed offer
                offer = intent.get("guaranteed_unshielded_offer")
                if offer:
                    # Create signature
                    payload = get_unshielded_signing_payload(seg_id, intent)
                    sig = wallet.unshielded.sign_seg_intent(payload)
                    offer["signatures"] = [sig]

                # Sign fallible offer if exists
                f_offer = intent.get("fallible_unshielded_offer")
                if f_offer:
                    payload = get_unshielded_signing_payload(seg_id, intent)
                    sig = wallet.unshielded.sign_seg_intent(payload)
                    f_offer["signatures"] = [sig]

        # 2. Serialize to Midnight Transaction format (tagged)
        midnight_tx_bytes = serialize_transaction(tx_data)

        # 3. Wrap in Substrate extrinsic (pallet 5, call 0)
        serializer = MidnightTransactionSerializer()
        return serializer.serialize_raw_midnight_tx(midnight_tx_bytes)

    async def _wait_for_receipt(self, tx_hash: str, timeout: int = 120) -> "TransactionReceipt":
        """Poll Indexer until tx is finalized."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                txs = await self._client.indexer.get_transactions(hash=tx_hash)
                if txs and txs[0].transaction_result:
                    tx = txs[0]
                    from noxipher.tx.models import TransactionReceipt

                    return TransactionReceipt(
                        hash=tx.hash,
                        block_height=tx.block.height if tx.block else None,
                        block_hash=tx.block.hash if tx.block else None,
                        status=tx.transaction_result.status,
                        fee_paid=(int(tx.fees.get("paid_fees", 0)) if tx.fees else 0),
                    )
            except Exception:
                pass
            await asyncio.sleep(2)
        raise TransactionTimeoutError(f"Timeout waiting for tx {tx_hash}")
