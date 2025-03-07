from bitcoinrpc.authproxy import AuthServiceProxy

# Configurazione RPC
RPC_USER = '...'
RPC_PASSWORD = '...'
RPC_ADDRESS = '...'
RPC_PORT = 8332

def get_rpc_connection():
    """
    Crea e restituisce una connessione RPC al nodo Bitcoin.
    """
    url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_ADDRESS}:{RPC_PORT}"
    return AuthServiceProxy(url)
