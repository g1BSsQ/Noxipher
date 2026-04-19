"""
DApp Connector — interface with Midnight DApps.

DApp Connector pattern (from Midnight web3 docs):
  1. DApp requests wallet connection
  2. Wallet (Noxipher) provides:
     - getCoinPublicKey(): string
     - getEncryptionPublicKey(): string
     - balanceTx(tx, ttl): BalancedTx
     - submitTx(tx): string → tx hash

TTL default: 30 minutes = 1800 seconds
"""

from typing import TYPE_CHECKING, Any

from noxipher.wallet.wallet import MidnightWallet

if TYPE_CHECKING:
    from noxipher.core.client import NoxipherClient

DEFAULT_TTL_SECONDS = 1800  # 30 minutes


class DAppConnector:
    """
    DApp Connector interface for Midnight smart contracts.
    Allows DApps to interact with wallet through standard interface.
    """

    def __init__(self, wallet: MidnightWallet, client: NoxipherClient) -> None:
        self._wallet = wallet
        self._client = client

    def get_coin_public_key(self) -> str:
        """Return hex-encoded coin public key (32 bytes)."""
        return self._wallet.shielded._keys.coin_public_key.hex()

    def get_encryption_public_key(self) -> str:
        """Return hex-encoded encryption public key (32 bytes)."""
        return self._wallet.shielded._keys.encryption_public_key.hex()

    async def balance_transaction(
        self, unbound_tx: dict[str, Any], ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> dict[str, Any]:
        """
        Balance unbound transaction — add inputs/outputs to cover fees.
        """
        from noxipher.core.exceptions import TransactionError

        # 1. Extract intent
        # Supports both wrapped and raw StandardTransaction
        stx = unbound_tx.get("standard", unbound_tx)
        intents = stx.get("intents", {})
        if not intents:
            stx["intents"] = {"0": {"ttl": ttl_seconds, "actions": []}}
            intents = stx["intents"]

        intent = intents.get("0") or intents.get(0)
        if not intent:
            intent = {"ttl": ttl_seconds, "actions": []}
            intents["0"] = intent

        # 2. Ensure guaranteed_unshielded_offer exists
        offer = intent.get("guaranteed_unshielded_offer")
        if not offer:
            offer = {"inputs": [], "outputs": [], "signatures": []}
            intent["guaranteed_unshielded_offer"] = offer

        # 3. Calculate current balance
        inputs_val = sum(int(i["value"]) for i in offer.get("inputs", []))
        outputs_val = sum(int(o["value"]) for o in offer.get("outputs", []))

        # Fetch minimum fee from network config
        fee = self._client.config.min_fee
        required = outputs_val + fee

        if inputs_val < required:
            # 4. Fetch and add more UTXOs (Largest First)
            utxos = await self._wallet.unshielded.get_utxos(self._client.indexer)

            # Filter by token type (NIGHT is 0 in StandardTransaction) and unused
            used_outpoints = {(i["intent_hash"].hex(), i["output_no"]) for i in offer["inputs"]}

            eligible = []
            for utxo in utxos:
                i_hash = utxo.get("intentHash") or utxo.get("intent_hash") or ("00" * 32)
                o_no = utxo.get("outputNo") or utxo.get("output_no") or 0

                # Check token type (NIGHT is all zeros)
                u_token = utxo.get("token_type") or utxo.get("tokenType") or ("00" * 32)
                if isinstance(u_token, dict):
                    u_token = u_token.get("hex", "00" * 32)

                if (i_hash, o_no) not in used_outpoints and u_token == ("00" * 32):
                    eligible.append(utxo)

            # Sort descending by value to minimize inputs
            eligible.sort(key=lambda x: int(x.get("value", 0)), reverse=True)

            added_val = 0
            for utxo in eligible:
                i_hash = utxo.get("intentHash") or utxo.get("intent_hash") or ("00" * 32)
                o_no = utxo.get("outputNo") or utxo.get("output_no") or 0

                offer["inputs"].append(
                    {
                        "value": int(utxo["value"]),
                        "owner": self._wallet.unshielded.public_key,
                        "type_": 0,
                        "intent_hash": bytes.fromhex(i_hash),
                        "output_no": int(o_no),
                    }
                )
                added_val += int(utxo["value"])
                if inputs_val + added_val >= required:
                    break

            inputs_val += added_val
            if inputs_val < required:
                msg = (
                    f"Insufficient funds to balance transaction. "
                    f"Need {required}, have {inputs_val}"
                )
                raise TransactionError(msg)

        # 5. Add change output
        if inputs_val > required:
            offer["outputs"].append(
                {
                    "value": inputs_val - required,
                    "owner": self._wallet.unshielded.public_key,
                    "type_": 0,
                }
            )

        # 6. Set TTL
        intent["ttl"] = ttl_seconds

        # Return the potentially modified unbound_tx
        return unbound_tx

    async def submit_transaction(self, finalized_tx: dict[str, Any]) -> str:
        """Submit finalized transaction → tx hash."""
        raw_bytes = self._client.tx._serialize_transaction(finalized_tx, self._wallet)
        return await self._client.node.submit_extrinsic(raw_bytes)

    def as_provider_dict(self) -> dict[str, Any]:
        """
        Return provider dict compatible with Midnight.js contracts API.

        MidnightProvider interface:
          getCoinPublicKey: () → string
          getEncryptionPublicKey: () → string
          balanceTx: (tx, ttl) → Promise<BalancedTx>
          submitTx: (tx) → Promise<string>
        """
        return {
            "getCoinPublicKey": self.get_coin_public_key,
            "getEncryptionPublicKey": self.get_encryption_public_key,
            "balanceTx": self.balance_transaction,
            "submitTx": self.submit_transaction,
        }
