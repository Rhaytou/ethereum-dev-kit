"""
ethereum-client/client.py
=========================
Thin re-export of core.rpc for the ethereum-client module.

The EthereumRPC class and get_rpc_client() factory now live in core/rpc.py.
This file exists so the ethereum-client module remains a usable entry point
and so running `python3 client.py` directly still works.

Importing from this module:
    from core.rpc import EthereumRPC, get_rpc_client
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.rpc import EthereumRPC, get_rpc_client


# ---------------------------------------------------------------------------
# Entry point — only runs when executed directly, never on import
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rpc = get_rpc_client()

    info = rpc.eth_syncing()
    print(json.dumps(info, indent=4))


# ---------------------------------------------------------------------------
# RPC commands
# ---------------------------------------------------------------------------
'''
web3_clientVersion
web3_sha3
net_version
net_listening
net_peerCount
eth_protocolVersion
eth_syncing
eth_coinbase
eth_chainId
eth_mining
eth_hashrate
eth_gasPrice
eth_accounts
eth_blockNumber
eth_getBalance
eth_getStorageAt
eth_getTransactionCount
eth_getBlockTransactionCountByHash
eth_getBlockTransactionCountByNumber
eth_getUncleCountByBlockHash
eth_getUncleCountByBlockNumber
eth_getCode
eth_sign
eth_sendTransaction
eth_signTransaction
eth_sendRawTransaction
eth_call
eth_estimateGas
eth_getBlockByNumber
eth_getBlockByHash
eth_getTransactionByBlockNumberAndIndex
eth_getTransactionByBlockHashAndIndex
eth_getTransactionByHash
eth_getTransactionReceipt
eth_getUncleByBlockNumberAndIndex
eth_getUncleByBlockHashAndIndex
eth_newBlockFilter
eth_getFilterChanges
eth_uninstallFilter
eth_newPendingTransactionFilter
eth_getFilterChanges
eth_uninstallFilter
eth_newFilter
eth_getFilterLogs
eth_getLogs
eth_subscribe
'''
























