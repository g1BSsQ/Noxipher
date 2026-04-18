"""
MidnightWallet — Facade for 3 sub-wallets.

CONFIRMED from Counter CLI source (Apr 2026):
  1. keys = HDWallet.deriveKeysFromSeed(seed)
  2. shieldedSecretKeys = ledger.ZswapSecretKeys.fromSeed(keys[Roles.Zswap])
  3. dustSecretKey = ledger.DustSecretKey.fromSeed(keys[Roles.Dust])
  4. unshieldedKeystore = createKeystore(keys[Roles.NightExternal], networkId)
"""
from __future__ import annotations

from noxipher.core.config import Network
from noxipher.crypto.keys import SpendingKey
from noxipher.wallet.dust import DustWallet
from noxipher.wallet.shielded import ShieldedWallet
from noxipher.wallet.unshielded import UnshieldedWallet


class MidnightWallet:
    """
    Unified wallet facade for Midnight 3-token system.

    Addresses:
      wallet.unshielded.address → mn_addr_preprod1...
      wallet.shielded.address   → mn_shield-addr_preprod1...
      wallet.dust.address       → mn_dust_preprod1...
    """

    def __init__(self, mnemonic: str, network: Network, account: int = 0) -> None:
        # Derive spending key (64-byte BIP39 seed internally)
        self._spending_key = SpendingKey.from_mnemonic(mnemonic, network)

        # Initialize 3 sub-wallets
        self._unshielded = UnshieldedWallet(
            key_bytes=self._spending_key.night_key,
            network=network,
        )
        self._shielded = ShieldedWallet(
            shielded_seed=self._spending_key.zswap_seed,
            network=network,
        )
        self._dust = DustWallet(
            dust_seed=self._spending_key.dust_seed,
            network=network,
        )
        self._network = network

    @property
    def unshielded(self) -> UnshieldedWallet:
        """Unshielded NIGHT wallet."""
        return self._unshielded

    @property
    def shielded(self) -> ShieldedWallet:
        """Shielded privacy wallet."""
        return self._shielded

    @property
    def dust(self) -> DustWallet:
        """DUST fee wallet."""
        return self._dust

    @property
    def network(self) -> Network:
        """Current network."""
        return self._network

    @classmethod
    def from_mnemonic(cls, mnemonic: str, network: Network) -> "MidnightWallet":
        """Create wallet from BIP39 mnemonic (24 words)."""
        return cls(mnemonic=mnemonic, network=network)

    @classmethod
    def generate(cls, network: Network) -> tuple["MidnightWallet", str]:
        """
        Generate new random wallet.

        Returns:
            (wallet, mnemonic) — SAVE the mnemonic immediately!
        """
        from mnemonic import Mnemonic

        m = Mnemonic("english")
        mnemonic = m.generate(strength=256)  # 24 words
        return cls(mnemonic=mnemonic, network=network), mnemonic
