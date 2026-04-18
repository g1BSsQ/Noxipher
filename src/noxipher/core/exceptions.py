class NoxipherError(Exception):
    """Base class for all Noxipher exceptions."""

    pass


class ConfigurationError(NoxipherError):
    """Raised when configuration is invalid or missing."""

    pass


class ConnectionError(NoxipherError):
    pass


class InvalidMnemonicError(NoxipherError):
    pass


class KeyDerivationError(NoxipherError):
    pass


class CryptographyError(NoxipherError):
    """Raised during cryptographic failures (e.g. invalid keys)."""

    pass


class NetworkError(NoxipherError):
    """Raised when network requests fail."""

    pass


class NodeError(NoxipherError):
    """Raised when the Midnight Node returns an error."""

    pass


class IndexerError(NoxipherError):
    """Raised when the Indexer GraphQL API returns an error."""

    pass


class ProofServerError(NoxipherError):
    """Raised when the ZK Proof Server returns an error."""

    pass


class ProofError(NoxipherError):
    pass


class TransactionError(NoxipherError):
    """Raised during transaction construction or submission failures."""

    pass


class TransactionTimeoutError(TransactionError):
    pass


class ContractError(NoxipherError):
    """Raised when a smart contract interaction fails."""

    pass


class WalletError(NoxipherError):
    """Raised for wallet-related issues (e.g. insufficient funds, locked wallet)."""

    pass


class AddressError(NoxipherError):
    """Raised when an address format is invalid."""

    pass
