# Getting Started

This guide will walk you through installing Noxipher and running your first Midnight blockchain interaction.

## Installation

Noxipher is available on PyPI. You can install it using `pip` or `uv`:

```bash
# Using pip
pip install noxipher

# Using uv
uv pip install noxipher
```

### Optional Dependencies
If you need to interact directly with the Substrate node (for example, fetching raw block data or submitting custom extrinsics), you need to install the `node` optional dependencies. This requires the Rust toolchain to build the cryptography bindings:

```bash
pip install "noxipher[node]"
```

## Basic Usage

The primary entry point to the SDK is the `NoxipherClient`. It handles the connections to the Midnight Indexer and Node RPC.

### Connecting to the Network

Noxipher uses `asyncio`. Here is how you initialize the client and connect to the Pre-Production network:

```python
import asyncio
from noxipher.core.client import NoxipherClient
from noxipher.core.config import Network

async def main():
    # Context manager ensures connections are properly closed
    async with NoxipherClient(network=Network.PREPROD) as client:
        print("Connected to Midnight Pre-Production network!")
        
        # Example: Get network parameters
        # params = await client.get_network_params()
        # print(params)

if __name__ == "__main__":
    asyncio.run(main())
```

### Managing Wallets

Noxipher provides a robust `MidnightWallet` class to manage keys and sign transactions.

```python
from noxipher.wallet.wallet import MidnightWallet
from noxipher.core.config import Network

# Create a wallet from a 24-word BIP39 mnemonic phrase
mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
wallet = MidnightWallet.from_mnemonic(mnemonic, Network.PREPROD)

print(f"Your unshielded (NIGHT) address: {wallet.public_address}")
```

### Putting it together

You can use the wallet and the client to query balances and submit transactions:

```python
import asyncio
from noxipher.core.client import NoxipherClient
from noxipher.wallet.wallet import MidnightWallet
from noxipher.core.config import Network

async def main():
    wallet = MidnightWallet.from_mnemonic("your 24 words...", Network.PREPROD)
    
    async with NoxipherClient(network=Network.PREPROD) as client:
        # Get unshielded NIGHT balance
        balance = await client.get_balance(wallet)
        print(f"Current Balance: {balance} NIGHT/lovelace")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps
For detailed documentation on specific modules, please refer to the [API Reference](api/core.md).
