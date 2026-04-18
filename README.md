# Noxipher 🌑

[![CI](https://github.com/g1BSsQ/Noxipher/actions/workflows/ci.yml/badge.svg)](https://github.com/g1BSsQ/Noxipher/actions/workflows/ci.yml)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Noxipher** is a professional-grade Python SDK for the **Midnight Network**, a privacy-focused blockchain. It provides a robust, asynchronous interface for interacting with Midnight nodes, indexers, and proof servers.

## 🚀 Features

- **Asynchronous First**: Built with `httpx`, `gql`, and `websockets` for high-performance async workflows.
- **Byte-Perfect SCALE Serialization**: Custom implementation of Midnight's `ScaleBigInt` and tagged serialization protocol (v5.0 spec).
- **Comprehensive Wallet Support**: Unified management of NIGHT (unshielded), ZK (shielded), and DUST (fee) tokens.
- **Smart Transaction Building**: Automatic UTXO discovery and selection for unshielded transfers.
- **Node & Indexer Integration**: Direct interaction with Substrate-based node RPCs and GraphQL indexers.

## 📦 Installation

```bash
# Basic installation
pip install noxipher

# With Node interaction support (requires Rust toolchain for bindings)
pip install "noxipher[node]"
```

## 🛠️ Quick Start

```python
import asyncio
from noxipher.core.client import NoxipherClient
from noxipher.wallet.wallet import MidnightWallet
from noxipher.core.config import Network

async def main():
    # Initialize client (defaults to PREPROD)
    async with NoxipherClient(network=Network.PREPROD) as client:
        # Load wallet from mnemonic
        wallet = MidnightWallet.from_mnemonic("your 24 words...", Network.PREPROD)
        
        # Check unshielded balance
        balance = await client.get_balance(wallet)
        print(f"Balance: {balance}")
        
        # Send an unshielded NIGHT transfer
        receipt = await client.send_unshielded_transaction(
            wallet,
            recipient_address="mn_addr_preprod1...",
            amount=1_000_000  # 1 NIGHT
        )
        print(f"Transaction finalized in block {receipt.block_height}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🏗️ Architecture

Noxipher coordinates three main services:
1. **Midnight Node**: For extrinsic submission and chain state.
2. **Indexer**: For transaction history and UTXO discovery.
3. **Proof Server**: For generating Zero-Knowledge proofs (required for shielded transactions).

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run SCALE serialization validation
python tests/unit/test_scale.py
```

## 📄 License

MIT © [g1BSsQ](mailto:hungboycl@gmail.com)
