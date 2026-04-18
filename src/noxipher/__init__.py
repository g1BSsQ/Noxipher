"""
Noxipher — Python SDK for Midnight Blockchain.

Public API surface (per NOXIPHER_SPEC_v5_0.md Section 19).
"""

from noxipher._version import __version__

# ─── Address ───
from noxipher.address.bech32m import decode_address, encode_address, validate_address

# ─── Contract ───
from noxipher.contract.compact import CompactContract, ContractABI
from noxipher.contract.instance import ContractInstance
from noxipher.contract.service import ContractService
from noxipher.core.client import NoxipherClient

# ─── Core ───
from noxipher.core.config import NETWORK_CONFIGS, Network, NetworkConfig
from noxipher.core.exceptions import (
    AddressError,
    ConnectionError,
    ContractError,
    IndexerError,
    InvalidMnemonicError,
    KeyDerivationError,
    NoxipherError,
    ProofError,
    TransactionError,
    TransactionTimeoutError,
    WalletError,
)
from noxipher.core.health import HealthStatus, ServiceHealth
from noxipher.crypto.hash import blake2_256
from noxipher.crypto.jubjub import DustSecretKey, ZswapSecretKeys

# ─── Crypto ───
from noxipher.crypto.keys import (
    KeyDerivation,
    Roles,
    SpendingKey,
    Sr25519Signer,
)

# ─── DApp ───
from noxipher.dapp.connector import DAppConnector

# ─── Indexer ───
from noxipher.indexer.client import IndexerClient
from noxipher.indexer.models import Block, DustGenerationStatus, Transaction

# ─── Node ───
from noxipher.node.client import NodeClient

# ─── Proof ───
from noxipher.proof.client import ProofServerClient
from noxipher.token.dust import DUSTToken

# ─── Token ───
from noxipher.token.night import NIGHTToken
from noxipher.token.shielded import ShieldedToken

# ─── Transaction ───
from noxipher.tx.builder import TransactionBuilder
from noxipher.tx.models import TransactionReceipt
from noxipher.wallet.balance import TokenBalance, WalletState
from noxipher.wallet.dust import DustWallet
from noxipher.wallet.keystore import Keystore
from noxipher.wallet.shielded import ShieldedWallet
from noxipher.wallet.sync import WalletSyncer
from noxipher.wallet.unshielded import UnshieldedWallet

# ─── Wallet ───
from noxipher.wallet.wallet import MidnightWallet

__all__ = [
    # Version
    "__version__",
    # Core
    "Network",
    "NetworkConfig",
    "NETWORK_CONFIGS",
    "NoxipherClient",
    "HealthStatus",
    "ServiceHealth",
    # Exceptions
    "NoxipherError",
    "ConnectionError",
    "InvalidMnemonicError",
    "KeyDerivationError",
    "TransactionError",
    "TransactionTimeoutError",
    "ProofError",
    "IndexerError",
    "ContractError",
    "WalletError",
    "AddressError",
    # Address
    "encode_address",
    "decode_address",
    "validate_address",
    # Crypto
    "KeyDerivation",
    "Sr25519Signer",
    "SpendingKey",
    "Roles",
    "ZswapSecretKeys",
    "DustSecretKey",
    "blake2_256",
    # Wallet
    "MidnightWallet",
    "UnshieldedWallet",
    "ShieldedWallet",
    "DustWallet",
    "Keystore",
    "WalletState",
    "TokenBalance",
    "WalletSyncer",
    # Indexer
    "IndexerClient",
    "Block",
    "Transaction",
    "DustGenerationStatus",
    # Node
    "NodeClient",
    # TX
    "TransactionBuilder",
    "TransactionReceipt",
    # Proof
    "ProofServerClient",
    # Contract
    "CompactContract",
    "ContractABI",
    "ContractInstance",
    "ContractService",
    # Token
    "NIGHTToken",
    "DUSTToken",
    "ShieldedToken",
    # DApp
    "DAppConnector",
]
