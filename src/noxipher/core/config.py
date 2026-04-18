from enum import StrEnum

from pydantic import AnyUrl, BaseModel, Field, HttpUrl


class Network(StrEnum):
    MAINNET = "mainnet"
    TESTNET = "testnet"
    PREPROD = "preprod"
    PREVIEW = "preview"
    DEVNET = "devnet"
    LOCAL = "local"
    UNDEPLOYED = "undeployed"


class NetworkConfig(BaseModel):
    name: str
    network: Network
    node_ws_url: AnyUrl
    indexer_ws_url: AnyUrl
    indexer_http_url: HttpUrl
    proof_server_url: HttpUrl
    hosted_proof_server_url: HttpUrl | None = None
    coin_type: int = Field(default=877, description="SLIP-0044 Coin Type")


NETWORK_CONFIGS: dict[Network, NetworkConfig] = {
    Network.MAINNET: NetworkConfig(
        name="Midnight Mainnet",
        network=Network.MAINNET,
        node_ws_url="wss://rpc.midnight.network",
        indexer_ws_url="wss://indexer.midnight.network/api/v4/graphql",
        indexer_http_url="https://indexer.midnight.network/api/v4/graphql",
        proof_server_url="http://localhost:6300",
        hosted_proof_server_url="https://proof.mainnet.midnight.network",
    ),
    Network.PREVIEW: NetworkConfig(
        name="Midnight Preview",
        network=Network.PREVIEW,
        node_ws_url="wss://rpc.preview.midnight.network",
        indexer_ws_url="wss://indexer.preview.midnight.network/api/v4/graphql",
        indexer_http_url="https://indexer.preview.midnight.network/api/v4/graphql",
        proof_server_url="http://localhost:6300",
    ),
    Network.PREPROD: NetworkConfig(
        name="Midnight Preprod",
        network=Network.PREPROD,
        node_ws_url="wss://rpc.preprod.midnight.network",
        indexer_ws_url="wss://indexer.preprod.midnight.network/api/v4/graphql",
        indexer_http_url="https://indexer.preprod.midnight.network/api/v4/graphql",
        proof_server_url="http://localhost:6300",
    ),
    Network.TESTNET: NetworkConfig(
        name="Midnight Testnet",
        network=Network.TESTNET,
        node_ws_url="wss://rpc.testnet.midnight.network",
        indexer_ws_url="wss://indexer.testnet.midnight.network/api/v4/graphql",
        indexer_http_url="https://indexer.testnet.midnight.network/api/v4/graphql",
        proof_server_url="http://localhost:6300",
    ),
    Network.DEVNET: NetworkConfig(
        name="Midnight Devnet",
        network=Network.DEVNET,
        node_ws_url="wss://rpc.devnet.midnight.network",
        indexer_ws_url="wss://indexer.devnet.midnight.network/api/v4/graphql",
        indexer_http_url="https://indexer.devnet.midnight.network/api/v4/graphql",
        proof_server_url="http://localhost:6300",
    ),
    Network.LOCAL: NetworkConfig(
        name="Midnight Local",
        network=Network.LOCAL,
        node_ws_url="ws://127.0.0.1:9944",
        indexer_ws_url="ws://127.0.0.1:8088/api/v4/graphql",
        indexer_http_url="http://127.0.0.1:8088/api/v4/graphql",
        proof_server_url="http://localhost:6300",
    ),
    Network.UNDEPLOYED: NetworkConfig(
        name="Midnight Undeployed",
        network=Network.UNDEPLOYED,
        node_ws_url="ws://localhost:9944",
        indexer_ws_url="ws://localhost:8088/api/v4/graphql",
        indexer_http_url="http://localhost:8088/api/v4/graphql",
        proof_server_url="http://localhost:6300",
    ),
}
