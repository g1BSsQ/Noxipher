"""Unit tests for core config module."""

from noxipher.core.config import NETWORK_CONFIGS, Network


class TestNetwork:
    """Test Network enum."""

    def test_network_values(self) -> None:
        assert Network.MAINNET == "mainnet"
        assert Network.PREPROD == "preprod"
        assert Network.PREVIEW == "preview"
        assert Network.UNDEPLOYED == "undeployed"

    def test_network_from_string(self) -> None:
        assert Network("preprod") == Network.PREPROD

    def test_all_networks_have_configs(self) -> None:
        for network in Network:
            assert network in NETWORK_CONFIGS


class TestNetworkConfig:
    """Test NetworkConfig model."""

    def test_preprod_config(self) -> None:
        config = NETWORK_CONFIGS[Network.PREPROD]
        assert config.network == Network.PREPROD
        assert "preprod" in str(config.node_ws_url)
        assert "preprod" in str(config.indexer_http_url)
        assert str(config.proof_server_url) == "http://localhost:6300/"

    def test_mainnet_has_hosted_proof(self) -> None:
        config = NETWORK_CONFIGS[Network.MAINNET]
        assert config.hosted_proof_server_url is not None
        assert "mainnet" in str(config.hosted_proof_server_url)

    def test_undeployed_is_localhost(self) -> None:
        config = NETWORK_CONFIGS[Network.UNDEPLOYED]
        assert "localhost" in str(config.node_ws_url)
        assert "localhost" in str(config.indexer_http_url)

    def test_indexer_urls_have_v4(self) -> None:
        """Verify all Indexer URLs point to v4 API."""
        for config in NETWORK_CONFIGS.values():
            assert "/api/v4/" in str(config.indexer_http_url)
