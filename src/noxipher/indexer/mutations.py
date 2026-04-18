"""
GraphQL mutation strings for Midnight Indexer v4.
"""

CONNECT_WALLET = """
mutation ConnectWallet($viewingKey: ViewingKey!) {
    connect(viewingKey: $viewingKey)
}
"""

DISCONNECT_WALLET = """
mutation DisconnectWallet($sessionId: String!) {
    disconnect(sessionId: $sessionId)
}
"""
