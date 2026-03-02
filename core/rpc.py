"""
core/rpc.py
===========
Ethereum JSON-RPC client for the Ethereum Dev Kit.

The EthereumRPC class and the get_rpc_client() factory live here.
Both ethereum-client/client.py and ethereum-transactions/tx_templates.py
import from this module — the class is never redefined elsewhere.

Usage:
    from core.rpc import get_rpc_client

    rpc = get_rpc_client()
    syncing = rpc.eth_syncing()
    result  = rpc.call("eth_blockNumber", [])
"""

import requests

from core.config import config


# ---------------------------------------------------------------------------
# RPC Client
# ---------------------------------------------------------------------------

class EthereumRPC:
    """JSON-RPC client for communicating with an Ethereum node."""

    def __init__(self, endpoint: str, session: requests.Session, timeout: int = 30):
        """Set up the RPC connection.

        Args:
            endpoint: Full URL of the Ethereum node RPC endpoint.
            session:  A requests.Session (no auth required for Geth HTTP).
            timeout:  Request timeout in seconds. Default: 30.
        """
        self._url     = endpoint
        self._session = session
        self._timeout = timeout
        self._session.headers.update({
            "Content-Type": "application/json"
        })

    def call(self, method: str, params: list = None, request_id: str = "ethereum-dev-kit"):
        """Send a JSON-RPC request and return the result.

        Args:
            method:     Ethereum RPC method name (e.g. "eth_blockNumber").
            params:     List of positional parameters. Default: [].
            request_id: Arbitrary string echoed back by the node.

        Returns:
            The `result` field of the JSON-RPC response.

        Raises:
            requests.HTTPError: On non-2xx HTTP responses.
            RuntimeError:       On RPC-level errors returned by the node.
        """
        if params is None:
            params = []

        payload = {
            "jsonrpc": "2.0",
            "id":      request_id,
            "method":  method,
            "params":  params,
        }

        response = self._session.post(
            self._url,
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()

        data = response.json()
        if data.get("error") is not None:
            raise RuntimeError(data["error"])

        return data["result"]

    # ------------------------------------------------------------------
    # Convenience shortcuts
    # ------------------------------------------------------------------

    def eth_syncing(self) -> dict | bool:
        """Shortcut for eth_syncing. Returns sync status or False if synced."""
        return self.call("eth_syncing")

    def eth_block_number(self) -> str:
        """Shortcut for eth_blockNumber. Returns latest block number as hex."""
        return self.call("eth_blockNumber")

    def eth_chain_id(self) -> str:
        """Shortcut for eth_chainId. Returns chain ID as hex."""
        return self.call("eth_chainId")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_rpc_client() -> EthereumRPC:
    """Create and return an EthereumRPC client configured from the environment.

    The endpoint is read from core.config (which loads .env).
    This is the single place in the project where an RPC session is built —
    never instantiate EthereumRPC directly with hardcoded values.

    Returns:
        A ready-to-use EthereumRPC instance.
    """
    session = requests.Session()
    return EthereumRPC(endpoint=config.rpc_endpoint, session=session)







