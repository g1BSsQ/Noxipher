"""
Noxipher — Python SDK for Midnight Blockchain.

Public API surface (per NOXIPHER_SPEC_v5_0.md Section 19).
"""
from noxipher._version import __version__

# ─── Core ───
from noxipher.core.config import Network, NetworkConfig, NETWORK_CONFIGS
from noxipher.core.client import NoxipherClient
from noxipher.core.exceptions import (
    NoxipherError,
    ConnectionError,
    InvalidMnemonicError,
    KeyDerivationError,
    TransactionError,
    TransactionTimeoutError,
    ProofError,
    IndexerError,
    ContractError,
    WalletError,
    AddressError,
)
from noxipher.core.health import HealthStatus, ServiceHealth

# ─── Address ───
from noxipher.address.bech32m import encode_address, decode_address, validate_address

# ─── Crypto ───
from noxipher.crypto.keys import (
    KeyDerivation,
    Sr25519Signer,
    SpendingKey,
    Roles,
)
from noxipher.crypto.jubjub import ZswapSecretKeys, DustSecretKey
from noxipher.crypto.hash import blake2_256

# ─── Wallet ───
from noxipher.wallet.wallet import MidnightWallet
from noxipher.wallet.unshielded import UnshieldedWallet
from noxipher.wallet.shielded import ShieldedWallet
from noxipher.wallet.dust import DustWallet
from noxipher.wallet.keystore import Keystore
from noxipher.wallet.balance import WalletState, TokenBalance
from noxipher.wallet.sync import WalletSyncer

# ─── Indexer ───
from noxipher.indexer.client import IndexerClient
from noxipher.indexer.models import Block, Transaction, DustGenerationStatus

# ─── Node ───
from noxipher.node.client import NodeClient

# ─── Transaction ───
from noxipher.tx.builder import TransactionBuilder
from noxipher.tx.models import TransactionReceipt

# ─── Proof ───
from noxipher.proof.client import ProofServerClient

# ─── Contract ───
from noxipher.contract.compact import CompactContract, ContractABI
from noxipher.contract.instance import ContractInstance
from noxipher.contract.service import ContractService

# ─── Token ───
from noxipher.token.night import NIGHTToken
from noxipher.token.dust import DUSTToken
from noxipher.token.shielded import ShieldedToken

# ─── DApp ───
from noxipher.dapp.connector import DAppConnector

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
