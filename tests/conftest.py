"""
pytest conftest — shared fixtures for all tests.
"""
import pytest

from noxipher.testing.testkit import TEST_MNEMONIC


@pytest.fixture
def test_mnemonic() -> str:
    """BIP39 test mnemonic (24 words)."""
    return TEST_MNEMONIC


@pytest.fixture
def test_seed_32() -> bytes:
    """32-byte all-zeros seed."""
    return bytes(32)
