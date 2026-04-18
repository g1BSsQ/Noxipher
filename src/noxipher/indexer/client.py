"""
IndexerClient — GraphQL HTTP + WebSocket client for Midnight Indexer v4.

Indexer v4 endpoints (confirmed Apr 2026):
  HTTP:  https://indexer.<network>.midnight.network/api/v4/graphql
  WS:    wss://indexer.<network>.midnight.network/api/v4/graphql/ws
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport
from tenacity import retry, stop_after_attempt, wait_exponential

from noxipher.core.config import NetworkConfig
from noxipher.core.exceptions import IndexerError
from noxipher.indexer.models import Block, DustGenerationStatus, Transaction
from noxipher.indexer.queries import GET_BLOCK, GET_DUST_STATUS, GET_TRANSACTIONS, GET_UTXOS
from noxipher.indexer.subscriptions import SUBSCRIBE_BLOCKS, SUBSCRIBE_SHIELDED_TXS


class IndexerClient:
    """
    GraphQL client for Midnight Indexer v4.

    Supports:
    - HTTP queries (block, transaction, UTXO, DUST)
    - WebSocket subscriptions (blocks, shielded transactions, ZSwap events)
    """

    def __init__(self, config: NetworkConfig) -> None:
        self._http_url = config.indexer_http_url
        self._ws_url = config.indexer_ws_url
        self._http_client: Client | None = None
        self._ws_client: Client | None = None

    async def __aenter__(self) -> IndexerClient:
        transport = AIOHTTPTransport(url=self._http_url)
        self._http_client = Client(transport=transport, fetch_schema_from_transport=False)
        await self._http_client.__aenter__()  # type: ignore[no-untyped-call]
        return self


    async def __aexit__(self, *args: object) -> None:
        if self._http_client:
            await self._http_client.__aexit__(*args)  # type: ignore[no-untyped-call]


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_block(self, height: int | None = None, hash_hex: str | None = None) -> Block:
        """Get block by height or hash. Default: latest block."""
        assert self._http_client is not None
        try:
            result = await self._http_client.execute_async(
                gql(GET_BLOCK),
                variable_values={"height": height, "hash": hash_hex},
            )
            return Block.model_validate(cast(dict[str, Any], result)["block"])

        except Exception as e:
            raise IndexerError(f"get_block failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_transactions(
        self,
        hash: str | None = None,
        address: str | None = None,
        limit: int = 10,
    ) -> list[Transaction]:
        """Get transactions by hash or address."""
        assert self._http_client is not None
        try:
            result = await self._http_client.execute_async(
                gql(GET_TRANSACTIONS),
                variable_values={"hash": hash, "address": address, "limit": limit},
            )
            data = cast(dict[str, Any], result)
            return [Transaction.model_validate(tx) for tx in data["transactions"]["nodes"]]

        except Exception as e:
            raise IndexerError(f"get_transactions failed: {e}") from e

    async def connect_wallet_session(self, viewing_key: str) -> str:
        """
        Open shielded wallet session with Indexer.

        Viewing key format: hex-encoded (coinPublicKey + encryptionPublicKey) — 64 bytes hex
        Returns: session_id string
        """
        mutation = gql("""
            mutation ConnectWallet($viewingKey: ViewingKey!) {
                connect(viewingKey: $viewingKey)
            }
        """)
        assert self._http_client is not None
        try:
            result = await self._http_client.execute_async(
                mutation,
                variable_values={"viewingKey": viewing_key},
            )
            return cast(str, cast(dict[str, Any], result)["connect"])

        except Exception as e:
            raise IndexerError(f"connect_wallet_session failed: {e}") from e

    async def disconnect_wallet_session(self, session_id: str) -> None:
        """Close shielded wallet session."""
        mutation = gql("""
            mutation DisconnectWallet($sessionId: String!) {
                disconnect(sessionId: $sessionId)
            }
        """)
        assert self._http_client is not None
        try:
            await self._http_client.execute_async(
                mutation,
                variable_values={"sessionId": session_id},
            )

        except Exception as e:
            raise IndexerError(f"disconnect_wallet_session failed: {e}") from e

    async def subscribe_blocks(self) -> AsyncIterator[Block]:
        """Subscribe to new blocks via WebSocket."""
        transport = WebsocketsTransport(url=self._ws_url)
        async with Client(transport=transport) as session:
            async for result in session.subscribe(gql(SUBSCRIBE_BLOCKS)):
                yield Block.model_validate(result["blockAdded"])

    async def subscribe_shielded_transactions(
        self, session_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream shielded transactions for wallet session.
        Returns ShieldedTransactionFound + ShieldedTransactionProgress events.
        """
        transport = WebsocketsTransport(url=self._ws_url)
        async with Client(transport=transport) as session:
            async for result in session.subscribe(
                gql(SUBSCRIBE_SHIELDED_TXS),
                variable_values={"sessionId": session_id},
            ):
                yield result["shieldedTransaction"]

    async def get_dust_status(self, cardano_stake_keys: list[str]) -> list[DustGenerationStatus]:
        """Query DUST generation status for Cardano stake keys."""
        assert self._http_client is not None
        result = await self._http_client.execute_async(
            gql(GET_DUST_STATUS),
            variable_values={"stakeKeys": cardano_stake_keys},
        )
        data = cast(dict[str, Any], result)
        return [DustGenerationStatus.model_validate(d) for d in data["dustStatus"]]


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_utxos(self, address: str) -> list[dict[str, Any]]:
        """Get unshielded UTXOs for an address."""
        assert self._http_client is not None
        try:
            result = await self._http_client.execute_async(
                gql(GET_UTXOS),
                variable_values={"address": address},
            )
            data = cast(dict[str, Any], result)
            return cast(list[dict[str, Any]], data["unshieldedUtxos"]["nodes"])


        except Exception as e:
            raise IndexerError(f"get_utxos failed: {e}") from e
