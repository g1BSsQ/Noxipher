"""
GraphQL query strings for Midnight Indexer v4.
"""

GET_BLOCK = """
query GetBlock($height: Int, $hash: String) {
    block(height: $height, hash: $hash) {
        height
        hash
        parentHash
        timestamp
    }
}
"""

GET_TRANSACTIONS = """
query GetTransactions($hash: String, $address: String, $limit: Int) {
    transactions(hash: $hash, address: $address, first: $limit) {
        nodes {
            hash
            block {
                height
                hash
            }
            transactionResult {
                status
                segments {
                    segmentId
                    status
                }
            }
            fees {
                paidFees
            }
            raw
            unshieldedCreatedOutputs {
                utxoId
                address
                value
                tokenType
            }
            unshieldedSpentOutputs {
                utxoId
                address
                value
                tokenType
            }
        }
    }
}
"""

GET_DUST_STATUS = """
query GetDustStatus($stakeKeys: [String!]!) {
    dustStatus(cardanoStakeKeys: $stakeKeys) {
        cardanoStakeKey
        isRegistered
        availableDust
        registeredUtxos {
            utxoId
            value
        }
    }
}
"""

GET_UTXOS = """
query GetUtxos($address: String!) {
    unshieldedUtxos(address: $address) {
        nodes {
            utxoId
            value
            tokenType
            intentHash
            outputNo
        }
    }
}
"""
