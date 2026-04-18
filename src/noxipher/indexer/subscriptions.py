"""
GraphQL subscription strings for Midnight Indexer v4.
"""

SUBSCRIBE_BLOCKS = """
subscription OnBlockAdded {
    blockAdded {
        height
        hash
        parentHash
        timestamp
    }
}
"""

SUBSCRIBE_SHIELDED_TXS = """
subscription OnShieldedTransaction($sessionId: String!) {
    shieldedTransaction(sessionId: $sessionId) {
        __typename
        ... on ShieldedTransactionFound {
            txHash
            relevantCoins {
                coinId
                value
                tokenType
            }
        }
        ... on ShieldedTransactionProgress {
            progress
            message
        }
    }
}
"""
