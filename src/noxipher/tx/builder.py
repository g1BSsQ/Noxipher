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
import secrets
from typing import TYPE_CHECKING, Any

from noxipher.core.exceptions import TransactionError, TransactionTimeoutError

if TYPE_CHECKING:
    from noxipher.core.client import NoxipherClient
    from noxipher.tx.models import TransactionReceipt
    from noxipher.wallet.wallet import MidnightWallet


class TransactionBuilder:
    \"\"\"Build and submit Midnight transactions. Pure Python.\"\"\"

    def __init__(self, client: "NoxipherClient") -> None:
        self._client = client

    async def transfer(
        self,
        wallet: "MidnightWallet",
        to: str,
        amount: int,
        shielded: bool = False,
        token_type: bytes = b"\x00" * 32,
        fee: int | None = None,
    ) -> "TransactionReceipt":
        \"\"\"
        Transfer NIGHT or other tokens.
        \"\"\"
        if shielded:
            # 1. Build shielded part (Zswap)
            unsigned_tx = await self._build_shielded_transfer(
                wallet, to, amount, token_type=token_type
            )
            # 2. Build unshielded part for fee (Midnight StandardTransaction requires fee)
            unshielded_part = await self._build_unshielded_transfer(
                wallet, wallet.unshielded.address, 0, fee=fee
            )
            # 3. Combine
            unsigned_tx["standard"] = unshielded_part["standard"]
            unsigned_tx["fee"] = unshielded_part["fee"]
            unsigned_tx["requires_unshielded_signature"] = True

            # 4. Prove
            proven_tx = await self._prove_transaction(unsigned_tx)
        else:
            # Unshielded transfers are direct and don't require the Proof Server
            proven_tx = await self._build_unshielded_transfer(
                wallet, to, amount, token_type=token_type, fee=fee
            )

        raw_bytes = self._serialize_transaction(proven_tx, wallet)
        tx_hash = await self._client.node.submit_extrinsic(raw_bytes)
        return await self._wait_for_receipt(tx_hash)

    async def call_contract(
        self,
        wallet: "MidnightWallet",
        contract_address: str,
        entry_point: str,
        args: dict[str, Any],
        fee: int | None = None,
    ) -> "TransactionReceipt":
        \"\"\"Call a contract entry point.\"\"\"
        # 1. Build unshielded part for gas fee
        unshielded_part = await self._build_unshielded_transfer(
            wallet, wallet.unshielded.address, 0, fee=fee
        )

        unsigned_tx = {
            "type": "contract_call",
            "contract_address": contract_address,
            "entry_point": entry_point,
            "args": args,
            "circuits": [],
            "requires_unshielded_signature": True,
            "standard": unshielded_part["standard"],
            "fee": unshielded_part["fee"],
        }
        proven_tx = await self._prove_transaction(unsigned_tx)
        raw_bytes = self._serialize_transaction(proven_tx, wallet)
        tx_hash = await self._client.node.submit_extrinsic(raw_bytes)
        return await self._wait_for_receipt(tx_hash)

    async def deploy_contract(
        self,
        wallet: "MidnightWallet",
        bytecode: bytes,
        initial_state: dict[str, Any] | bytes = b"",
        fee: int | None = None,
    ) -> "TransactionReceipt":
        \"\"\"Deploy a new smart contract.\"\"\"
        # 1. Build unshielded part for deployment fee
        unshielded_part = await self._build_unshielded_transfer(
            wallet, wallet.unshielded.address, 0, fee=fee
        )

        unsigned_tx: dict[str, Any] = {
            "type": "contract_deploy",
            "bytecode": bytecode,
            "initial_state": initial_state,
            "circuits": [],
            "requires_unshielded_signature": True,
            "standard": unshielded_part["standard"],
            "fee": unshielded_part["fee"],
        }
        # In Midnight, deployment doesn't usually need ZK proofs for the action itself,
        # but the transaction must still be balanced and signed.
        raw_bytes = self._serialize_transaction(unsigned_tx, wallet)
        tx_hash = await self._client.node.submit_extrinsic(raw_bytes)
        return await self._wait_for_receipt(tx_hash)

    async def _build_unshielded_transfer(
        self,
        wallet: "MidnightWallet",
        to_address: str,
        amount: int,
        fee: int | None = None,
        ttl: int = 1800,
        token_type: bytes = b"\x00" * 32,
    ) -> dict[str, Any]:
        \"\"\"
        Build unsigned unshielded transfer with optimized UTXO selection (Largest First).
        \"\"\"
        from noxipher.address.bech32m import decode_address

        # 1. Decode recipient address to get 32-byte public key/address
        try:
            _, _, recipient_bytes = decode_address(to_address)
        except Exception as e:
            raise TransactionError(f"Invalid recipient address: {e}") from e

        # 2. Fetch UTXOs
        utxos = await wallet.unshielded.get_utxos(self._client.indexer)

        # 3. Optimized Selection: Filter by token type and sort by value (Largest First)
        eligible = []
        for utxo in utxos:
            u_token = utxo.get("token_type") or utxo.get("tokenType") or ("00" * 32)
            if isinstance(u_token, dict):
                u_token = u_token.get("hex", "00" * 32)

            if u_token == token_type.hex():
                eligible.append(utxo)

        # 4. Optimized Selection
        # Total required including fee
        real_fee = fee if fee is not None else self._client.config.min_fee
        required = amount + real_fee

        # Step A: Try Exact Match to avoid fragmentation
        selected = []
        for utxo in eligible:
            if int(utxo.get("value", 0)) == required:
                selected = [utxo]
                current_total = required
                break

        # Step B: Fallback to Largest First (Greedy)
        if not selected:
            # Sort descending by value to minimize inputs
            eligible.sort(key=lambda x: int(x.get("value", 0)), reverse=True)
            current_total = 0
            for utxo in eligible:
                selected.append(utxo)
                current_total += int(utxo.get("value", 0))
                if current_total >= required:
                    break

        if current_total < required:
            raise TransactionError(
                f"Insufficient unshielded balance for amount+fee: {current_total} < {required}"
            )

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
        # Recipient output (Bug 2 Fix: Only add if amount > 0 to avoid Dust UTXOs)
        if amount > 0:
            outputs.append({"value": amount, "owner": recipient_bytes, "type_": 0})
        # Change output
        if current_total > required:
            outputs.append(
                {
                    "value": current_total - required,
                    "owner": wallet.unshielded.public_key,
                    "type_": 0,
                }
            )

        # 5. Structure for SCALE serialization
        # This dict[str, Any] matches the expected input of serialize_transaction in scale.py
        unshielded_offer = {
            "inputs": inputs,
            "outputs": outputs,
            "signatures": [],  # Will be filled by signer
        }

        # Bug 3 Fix: Real randomness and commitment for all unshielded envelopes
        rnd = secrets.token_bytes(32)
        from noxipher.crypto.jubjub import compute_binding_commitment

        intent = {
            "guaranteed_unshielded_offer": unshielded_offer,
            "ttl": ttl,
            "actions": [],
            "binding_commitment": compute_binding_commitment(rnd, value=real_fee),
        }

        # The StandardTransaction envelope
        stx = {
            "network_id": self._client.config.name,
            "intents": {"0": intent},
            "binding_randomness": rnd,
        }

        return {
            "type": "unshielded_transfer",
            "standard": stx,
            "fee": real_fee,
            "requires_unshielded_signature": True,
            "is_unshielded_only": True,
        }

    async def _build_shielded_transfer(
        self,
        wallet: "MidnightWallet",
        to: str,
        amount: int,
        ttl: int = 1800,
        token_type: bytes = b"\x00" * 32,
    ) -> dict[str, Any]:
        \"\"\"
        Build unsigned shielded transfer.

        Logic:
        1. Select shielded coins (Largest First).
        2. Extract witnesses (Merkle proofs).
        3. Create Zswap circuits (spend + output).
        4. Structure payload for Proof Server.
        \"\"\"
        # 1. Select coins (Largest First)
        coins = wallet.shielded_state.unspent_coins

        # Filter by token type
        eligible = [c for c in coins if c.token_type == token_type]

        # Sort descending by value to minimize spend circuits
        eligible.sort(key=lambda x: x.value, reverse=True)

        selected = []
        total_selected = 0
        for coin in eligible:
            selected.append(coin)
            total_selected += coin.value
            if total_selected >= amount:
                break

        if total_selected < amount:
            raise TransactionError(f"Insufficient shielded balance: {total_selected} < {amount}")

        # 2. Extract witnesses and create circuits
        # In Midnight, each spend and each output is a separate circuit.
        circuits = []
        from noxipher.crypto.fields import Fr
        from noxipher.crypto.poseidon import transient_hash

        # Spend circuits
        for coin in selected:
            if coin.merkle_tree_index is None:
                continue

            # Get real Merkle proof and root
            proof = wallet.shielded_state.merkle_tree.proof(coin.merkle_tree_index)
            root = wallet.shielded_state.merkle_tree.root()

            circuits.append(
                {
                    "id": "zswap_spend",
                    "private_inputs": {
                        "coin": coin.model_dump(),
                        "sk_coin": wallet.shielded._keys.coin_secret_key.hex(),
                        "merkle_proof": [p.hex() for p in proof],
                    },
                    "public_inputs": {
                        "nullifier": coin.compute_nullifier(
                            int.from_bytes(wallet.shielded._keys.coin_secret_key, "little")
                        ).hex(),
                        "merkle_root": root.hex(),
                    },
                }
            )

        from noxipher.address.bech32m import decode_address

        # Output circuit (recipient)
        # commitment = hash(token_type, value, recipient_pk, nonce)
        out_nonce = secrets.token_bytes(32)
        _, _, recipient_payload = decode_address(to)
        # Shielded payload is 64 bytes: coinPK (32) + encPK (32)
        recipient_coin_pk = recipient_payload[:32]

        out_commitment = transient_hash(
            [
                Fr.from_le_bytes(token_type),
                Fr(amount),
                Fr.from_le_bytes(recipient_coin_pk),
                Fr.from_le_bytes(out_nonce),
            ]
        ).to_bytes()

        circuits.append(
            {
                "id": "zswap_output",
                "private_inputs": {
                    "value": amount,
                    "recipient": to,
                    "nonce": out_nonce.hex(),
                },
                "public_inputs": {
                    "commitment": out_commitment.hex(),
                },
            }
        )

        # Change output if needed
        if total_selected > amount:
            change_nonce = secrets.token_bytes(32)
            change_val = total_selected - amount
            own_pk = wallet.shielded._keys.coin_public_key

            change_commitment = transient_hash(
                [
                    Fr.from_le_bytes(token_type),
                    Fr(change_val),
                    Fr.from_le_bytes(own_pk),
                    Fr.from_le_bytes(change_nonce),
                ]
            ).to_bytes()

            circuits.append(
                {
                    "id": "zswap_output",
                    "private_inputs": {
                        "value": change_val,
                        "recipient": wallet.shielded.address,
                        "nonce": change_nonce.hex(),
                    },
                    "public_inputs": {
                        "commitment": change_commitment.hex(),
                    },
                }
            )

        return {
            "type": "shielded_transfer",
            "from": wallet.shielded.address,
            "to": to,
            "amount": amount,
            "circuits": circuits,
            "requires_unshielded_signature": False,
            "guaranteed_hex": "",
            "fallible_hexes": [],
        }

    async def _prove_transaction(self, tx: dict[str, Any]) -> dict[str, Any]:
        \"\"\"Prove all segments via Proof Server HTTP API.\"\"\"
        from noxipher.proof.prover import ZKProver

        prover = ZKProver(self._client.proof)
        proven = await prover.prove_transaction(tx)
        return proven.model_dump()

    def _serialize_transaction(self, tx_data: dict[str, Any], wallet: "MidnightWallet") -> bytes:
        \"\"\"Serialize transaction to raw bytes with signing.\"\"\"
        from noxipher.crypto.jubjub import compute_binding_commitment
        from noxipher.tx.scale import (
            MidnightTransactionSerializer,
            get_unshielded_signing_payload,
            serialize_contract_args,
            serialize_transaction,
        )

        # 0. Handle contract deployment/call/shielded special structuring
        if tx_data.get("type") in ["contract_deploy", "contract_call"]:
            if "standard" not in tx_data:
                tx_data["standard"] = {
                    "network_id": self._client.config.name,
                    "intents": {
                        "0": {
                            "guaranteed_unshielded_offer": {
                                "inputs": [],
                                "outputs": [],
                                "signatures": [],
                            },
                            "ttl": 1800,
                            "actions": [],
                            "binding_commitment": b"\x00" * 32,
                        }
                    },
                    "binding_randomness": b"\x00" * 32,
                }

            if tx_data["type"] == "contract_deploy":
                action = {
                    "type": "deploy",
                    "bytecode": tx_data["bytecode"],
                    "initial_state": serialize_contract_args(tx_data.get("initial_state", b"")),
                }
            else:
                action = {
                    "type": "call",
                    "address": bytes.fromhex(tx_data["contract_address"]),
                    "entry_point": tx_data["entry_point"],
                    "args": serialize_contract_args(tx_data.get("args", b"")),
                }
            tx_data["standard"]["intents"]["0"]["actions"] = [action]

        elif tx_data.get("type") == "shielded_transfer":
            if "standard" not in tx_data:
                tx_data["standard"] = {
                    "network_id": self._client.config.name,
                    "intents": {
                        "0": {
                            "guaranteed_unshielded_offer": {
                                "inputs": [],
                                "outputs": [],
                                "signatures": [],
                            },
                            "ttl": 1800,
                            "actions": [],
                            "binding_commitment": b"\x00" * 32,
                        }
                    },
                    "binding_randomness": b"\x00" * 32,
                }

            # Integrate ZK Proofs into fallible_coins (StandardTransaction level)
            if "fallible_coins" not in tx_data["standard"]:
                tx_data["standard"]["fallible_coins"] = {}

            offer = {
                "spend_proofs": [
                    bytes.fromhex(p) if isinstance(p, str) else p
                    for p in tx_data.get("proof_hexes", {}).get("spends", [])
                ],
                "output_proofs": [
                    bytes.fromhex(p) if isinstance(p, str) else p
                    for p in tx_data.get("proof_hexes", {}).get("outputs", [])
                ],
                "zswap_memos": [],
                "merkle_root": tx_data.get("merkle_root", b"\x00" * 32),
            }
            tx_data["standard"]["fallible_coins"]["0"] = offer

        # 1. Finalize Cryptographic Binding (Unified Pedersen Commitment G^r * H^v)
        if "standard" in tx_data:
            stx = tx_data["standard"]
            rnd = secrets.token_bytes(32)
            fee = tx_data.get("fee", 0)
            
            stx["binding_randomness"] = rnd
            if "0" in stx["intents"]:
                commitment = compute_binding_commitment(rnd, value=fee)
                stx["intents"]["0"]["binding_commitment"] = commitment

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
        \"\"\"Poll Indexer until tx is finalized.\"\"\"
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                txs = await self._client.indexer.get_transactions(hash=tx_hash)
                if txs:
                    tx = txs[0]
                    if tx.transaction_result:
                        from noxipher.tx.models import TransactionReceipt

                        # Extract contract address from events
                        contract_addr = None
                        for event in (tx.events or []):
                            if event.get("type") == "ContractDeployed":
                                contract_addr = event.get("data", {}).get("address")
                                break

                        return TransactionReceipt(
                            hash=tx.hash,
                            block_height=tx.block.height if tx.block else None,
                            block_hash=tx.block.hash if tx.block else None,
                            status=tx.transaction_result.status,
                            fee_paid=(int(tx.fees.get("paid_fees", 0)) if tx.fees else 0),
                            contract_address=contract_addr,
                            events=tx.events or [],
                        )

            except Exception:
                pass
            await asyncio.sleep(2)
        raise TransactionTimeoutError(f"Timeout waiting for tx {tx_hash}")
