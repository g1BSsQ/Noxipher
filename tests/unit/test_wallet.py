"""Unit tests for wallet module."""
import pytest

from noxipher.core.config import Network
from noxipher.core.exceptions import WalletError
from noxipher.wallet.wallet import MidnightWallet

TEST_MNEMONIC = "abandon " * 23 + "art"


class TestMidnightWallet:
    """Test MidnightWallet facade."""

    def test_from_mnemonic(self) -> None:
        wallet = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        assert wallet.network == Network.PREPROD
        assert wallet.unshielded is not None
        assert wallet.shielded is not None
        assert wallet.dust is not None

    def test_addresses_are_different(self) -> None:
        wallet = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        unshielded_addr = wallet.unshielded.address
        shielded_addr = wallet.shielded.address
        dust_addr = wallet.dust.address
        assert unshielded_addr != shielded_addr
        assert unshielded_addr != dust_addr

    def test_address_prefixes(self) -> None:
        wallet = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        assert wallet.unshielded.address.startswith("mn_addr_preprod")
        assert wallet.shielded.address.startswith("mn_shield-addr_preprod")
        assert wallet.dust.address.startswith("mn_dust_preprod")

    def test_dust_cannot_transfer(self) -> None:
        wallet = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        assert wallet.dust.can_transfer() is False
        with pytest.raises(WalletError, match="cannot be transferred"):
            wallet.dust.transfer()

    def test_generate_wallet(self) -> None:
        wallet, mnemonic = MidnightWallet.generate(Network.PREPROD)
        assert len(mnemonic.split()) == 24
        assert wallet.network == Network.PREPROD

    def test_deterministic_addresses(self) -> None:
        """Same mnemonic → same addresses."""
        w1 = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        w2 = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        assert w1.unshielded.address == w2.unshielded.address
        assert w1.shielded.address == w2.shielded.address
        assert w1.dust.address == w2.dust.address

    def test_different_networks_different_addresses(self) -> None:
        """Same mnemonic, different networks → different addresses."""
        w_preprod = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        w_preview = MidnightWallet.from_mnemonic(TEST_MNEMONIC, Network.PREVIEW)
        assert w_preprod.unshielded.address != w_preview.unshielded.address
