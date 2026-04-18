from typing import TYPE_CHECKING

from .config import NETWORK_CONFIGS, Network, NetworkConfig
from .health import HealthStatus, ServiceHealth
from .logger import get_logger

if TYPE_CHECKING:
    from noxipher.tx.models import TransactionReceipt
    from noxipher.wallet.wallet import MidnightWallet


from noxipher.indexer.client import IndexerClient
from noxipher.node.client import NodeClient
from noxipher.proof.client import ProofServerClient
from noxipher.tx.builder import TransactionBuilder

logger = get_logger(__name__)


class NoxipherClient:
    """
    Main entry point for the Noxipher SDK.
    Coordinates the Indexer, Node, and Proof Server clients.
    """

    def __init__(
        self, network: Network = Network.PREPROD, custom_config: NetworkConfig | None = None
    ) -> None:
        self.config = custom_config or NETWORK_CONFIGS[network]
        logger.info("Initializing NoxipherClient", network=self.config.name)

        self.node = NodeClient(self.config)
        self.indexer = IndexerClient(self.config)
        self.proof = ProofServerClient(self.config.proof_server_url)
        self.tx = TransactionBuilder(self)


    async def __aenter__(self) -> "NoxipherClient":
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        """Establishes connections to all Midnight network components."""
        logger.info("Connecting to Midnight network components...")
        await self.node.connect()
        await self.indexer.__aenter__()
        await self.proof.__aenter__()
        logger.info("Connected to Node, Indexer, and Proof Server")

    async def disconnect(self) -> None:
        """Closes all network connections gracefully."""
        logger.info("Disconnecting NoxipherClient...")
        await self.node.disconnect()
        await self.indexer.__aexit__(None, None, None)
        await self.proof.__aexit__(None, None, None)

    async def check_health(self) -> ServiceHealth:
        """Checks the health of all network components."""
        node_health = await self.node.get_health()
        
        try:
            proof_health = await self.proof.health()
        except Exception:
            proof_health = {}

        # Simple heuristic for indexer health
        try:
            await self.indexer.get_block(height=0)
            indexer_ok = True
        except Exception:
            indexer_ok = False

        status = HealthStatus.OK if (node_health and indexer_ok) else HealthStatus.ERROR

        return ServiceHealth(
            status=status,
            node_connected=node_health is not None,
            indexer_connected=indexer_ok,
            proof_server_connected="version" in proof_health or proof_health.get("status") == "ok",
            details={"node": node_health, "proof_server": proof_health},
        )


    async def get_balance(self, wallet: "MidnightWallet") -> dict[str, int]:
        """Gets the unshielded balance of the given wallet."""
        return await wallet.unshielded.get_balance(self.indexer)

    async def send_unshielded_transaction(
        self, wallet: "MidnightWallet", recipient_address: str, amount: int
    ) -> "TransactionReceipt":
        """Sends an unshielded NIGHT transfer transaction."""
        return await self.tx.transfer(
            wallet=wallet, to=recipient_address, amount=amount, shielded=False
        )
