"""
ethereum-transactions/tx_templates.py
======================================
Ethereum transaction template builders for the Ethereum Dev Kit.

Each function builds and returns a ready-to-sign transaction dict.
No signing happens here — signing is the caller's responsibility.

Imports:
    core.config  — config.chain_id (from .env, never fetched live)
    core.rpc     — get_rpc_client() for live gas price, base fee, nonce
    core.crypto  — get_function_selector() for contract interaction calldata

Standards covered:
    Type 0x0 — Legacy         (EIP-155)   fee = gas * gasPrice
    Type 0x1 — Access List    (EIP-2930)  fee = gas * gasPrice + access list
    Type 0x2 — Dynamic Fee    (EIP-1559)  fee ≤ gas * maxFeePerGas

Use cases per type:
    ETH transfer          — EOA → EOA value transfer
    Contract deploy       — Deploy bytecode, no `to` field
    Contract interaction  — Call a function on a deployed contract

Run directly:
    python3 tx_templates.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import config
from core.rpc    import get_rpc_client
from core.crypto import get_function_selector


# ---------------------------------------------------------------------------
# Shared node helpers
# ---------------------------------------------------------------------------

def _get_gas_price() -> int:
    """Fetch current gas price from the node in wei."""
    return int(get_rpc_client().call("eth_gasPrice", []), 16)


def _get_base_fee() -> int:
    """Fetch the base fee of the latest block in wei."""
    block = get_rpc_client().call("eth_getBlockByNumber", ["latest", False])
    return int(block["baseFeePerGas"], 16)


def _get_nonce(address: str) -> int:
    """Fetch the current transaction count (nonce) for an address."""
    return int(get_rpc_client().call("eth_getTransactionCount", [address, "latest"]), 16)


# ---------------------------------------------------------------------------
# Type 0x0 — Legacy transaction (EIP-155)
# Fee model: fee = gas * gasPrice
# ---------------------------------------------------------------------------

def build_type0_eth_transfer(
    from_addr:  str,
    to_addr:    str,
    value_wei:  int,
    gas:        int = 21_000,
    gas_price:  int = None,
    nonce:      int = None,
    data:       str = "0x",
) -> dict:
    """Build a Type 0x0 legacy ETH transfer transaction.

    Args:
        from_addr:  Sender address (EIP-55 checksummed).
        to_addr:    Recipient address (EIP-55 checksummed).
        value_wei:  Amount to send in wei (e.g. 10**18 for 1 ETH).
        gas:        Gas limit. Default: 21_000.
        gas_price:  Gas price in wei. Fetched from node if None.
        nonce:      Sender nonce. Fetched from node if None.
        data:       Calldata. Default: '0x'.

    Returns:
        Transaction dict ready for signing.
    """
    return {
        "type":     "0x0",
        "chainId":  config.chain_id,
        "nonce":    nonce     if nonce     is not None else _get_nonce(from_addr),
        "from":     from_addr,
        "to":       to_addr,
        "value":    value_wei,
        "gas":      gas,
        "gasPrice": gas_price if gas_price is not None else _get_gas_price(),
        "data":     data,
    }


def build_type0_contract_deploy(
    from_addr:  str,
    bytecode:   str,
    gas:        int = 3_000_000,
    gas_price:  int = None,
    nonce:      int = None,
) -> dict:
    """Build a Type 0x0 legacy contract deployment transaction.

    No `to` field — its absence signals contract creation to the EVM.
    Do not set `value` unless the constructor is marked payable.

    Args:
        from_addr:  Deployer address (EIP-55 checksummed).
        bytecode:   Compiled contract bytecode, 0x-prefixed hex string.
        gas:        Gas limit. Default: 3_000_000.
        gas_price:  Gas price in wei. Fetched from node if None.
        nonce:      Sender nonce. Fetched from node if None.

    Returns:
        Transaction dict ready for signing.
    """
    return {
        "type":     "0x0",
        "chainId":  config.chain_id,
        "nonce":    nonce     if nonce     is not None else _get_nonce(from_addr),
        "from":     from_addr,
        "data":     bytecode,
        "gas":      gas,
        "gasPrice": gas_price if gas_price is not None else _get_gas_price(),
    }


def build_type0_contract_interaction(
    from_addr:     str,
    contract_addr: str,
    signature:     str,
    params:        str = "",
    value_wei:     int = 0,
    gas:           int = 100_000,
    gas_price:     int = None,
    nonce:         int = None,
) -> dict:
    """Build a Type 0x0 legacy contract interaction transaction.

    The 4-byte function selector is derived from `signature` via
    core.crypto.get_function_selector — never hardcoded by the caller.

    Args:
        from_addr:      Caller address (EIP-55 checksummed).
        contract_addr:  Target contract address (EIP-55 checksummed).
        signature:      Canonical function signature e.g. 'transfer(address,uint256)'.
        params:         ABI-encoded parameters as hex string (no 0x prefix). Default: ''.
        value_wei:      ETH to send in wei. Default: 0.
        gas:            Gas limit. Default: 100_000.
        gas_price:      Gas price in wei. Fetched from node if None.
        nonce:          Sender nonce. Fetched from node if None.

    Returns:
        Transaction dict ready for signing.
    """
    return {
        "type":     "0x0",
        "chainId":  config.chain_id,
        "nonce":    nonce     if nonce     is not None else _get_nonce(from_addr),
        "from":     from_addr,
        "to":       contract_addr,
        "value":    value_wei,
        "gas":      gas,
        "gasPrice": gas_price if gas_price is not None else _get_gas_price(),
        "data":     "0x" + get_function_selector(signature).hex() + params,
    }


# ---------------------------------------------------------------------------
# Type 0x1 — Access List transaction (EIP-2930)
# Fee model: fee = gas * gasPrice
# Access list: predeclare addresses + storage slots the tx will touch
# ---------------------------------------------------------------------------

def build_type1_eth_transfer(
    from_addr:   str,
    to_addr:     str,
    value_wei:   int,
    gas:         int  = 21_000,
    gas_price:   int  = None,
    nonce:       int  = None,
    data:        str  = "0x",
    access_list: list = None,
) -> dict:
    """Build a Type 0x1 access list ETH transfer transaction.

    Args:
        from_addr:   Sender address (EIP-55 checksummed).
        to_addr:     Recipient address (EIP-55 checksummed).
        value_wei:   Amount to send in wei.
        gas:         Gas limit. Default: 21_000.
        gas_price:   Gas price in wei. Fetched from node if None.
        nonce:       Sender nonce. Fetched from node if None.
        data:        Calldata. Default: '0x'.
        access_list: List of {address, storageKeys} dicts. Default: [].

    Returns:
        Transaction dict ready for signing.
    """
    return {
        "type":       "0x1",
        "chainId":    config.chain_id,
        "nonce":      nonce     if nonce     is not None else _get_nonce(from_addr),
        "from":       from_addr,
        "to":         to_addr,
        "value":      value_wei,
        "gas":        gas,
        "gasPrice":   gas_price if gas_price is not None else _get_gas_price(),
        "data":       data,
        "accessList": access_list if access_list is not None else [],
    }


def build_type1_contract_deploy(
    from_addr:   str,
    bytecode:    str,
    gas:         int  = 3_000_000,
    gas_price:   int  = None,
    nonce:       int  = None,
    access_list: list = None,
) -> dict:
    """Build a Type 0x1 access list contract deployment transaction.

    No `to` field — its absence signals contract creation to the EVM.
    Do not set `value` unless the constructor is marked payable.

    Args:
        from_addr:   Deployer address (EIP-55 checksummed).
        bytecode:    Compiled contract bytecode, 0x-prefixed hex string.
        gas:         Gas limit. Default: 3_000_000.
        gas_price:   Gas price in wei. Fetched from node if None.
        nonce:       Sender nonce. Fetched from node if None.
        access_list: List of {address, storageKeys} dicts. Default: [].

    Returns:
        Transaction dict ready for signing.
    """
    return {
        "type":       "0x1",
        "chainId":    config.chain_id,
        "nonce":      nonce     if nonce     is not None else _get_nonce(from_addr),
        "from":       from_addr,
        "data":       bytecode,
        "gas":        gas,
        "gasPrice":   gas_price if gas_price is not None else _get_gas_price(),
        "accessList": access_list if access_list is not None else [],
    }


def build_type1_contract_interaction(
    from_addr:     str,
    contract_addr: str,
    signature:     str,
    params:        str  = "",
    value_wei:     int  = 0,
    gas:           int  = 100_000,
    gas_price:     int  = None,
    nonce:         int  = None,
    access_list:   list = None,
) -> dict:
    """Build a Type 0x1 access list contract interaction transaction.

    Args:
        from_addr:      Caller address (EIP-55 checksummed).
        contract_addr:  Target contract address (EIP-55 checksummed).
        signature:      Canonical function signature e.g. 'transfer(address,uint256)'.
        params:         ABI-encoded parameters as hex string (no 0x prefix). Default: ''.
        value_wei:      ETH to send in wei. Default: 0.
        gas:            Gas limit. Default: 100_000.
        gas_price:      Gas price in wei. Fetched from node if None.
        nonce:          Sender nonce. Fetched from node if None.
        access_list:    List of {address, storageKeys} dicts. Default: [].

    Returns:
        Transaction dict ready for signing.
    """
    return {
        "type":       "0x1",
        "chainId":    config.chain_id,
        "nonce":      nonce     if nonce     is not None else _get_nonce(from_addr),
        "from":       from_addr,
        "to":         contract_addr,
        "value":      value_wei,
        "gas":        gas,
        "gasPrice":   gas_price if gas_price is not None else _get_gas_price(),
        "data":       "0x" + get_function_selector(signature).hex() + params,
        "accessList": access_list if access_list is not None else [],
    }


# ---------------------------------------------------------------------------
# Type 0x2 — Dynamic Fee transaction (EIP-1559)
# Fee model: fee ≤ gas * maxFeePerGas
# base fee is burned, priority fee goes to the validator
# ---------------------------------------------------------------------------

def build_type2_eth_transfer(
    from_addr:                str,
    to_addr:                  str,
    value_wei:                int,
    gas:                      int  = 21_000,
    max_priority_fee_per_gas: int  = None,
    max_fee_per_gas:          int  = None,
    nonce:                    int  = None,
    data:                     str  = "0x",
    access_list:              list = None,
) -> dict:
    """Build a Type 0x2 EIP-1559 ETH transfer transaction.

    If max_priority_fee_per_gas is not provided, defaults to eth_gasPrice.
    If max_fee_per_gas is not provided, defaults to baseFee + maxPriorityFee.

    Args:
        from_addr:                Sender address (EIP-55 checksummed).
        to_addr:                  Recipient address (EIP-55 checksummed).
        value_wei:                Amount to send in wei.
        gas:                      Gas limit. Default: 21_000.
        max_priority_fee_per_gas: Tip to validator in wei. Fetched if None.
        max_fee_per_gas:          Max total fee per gas in wei. Computed if None.
        nonce:                    Sender nonce. Fetched from node if None.
        data:                     Calldata. Default: '0x'.
        access_list:              List of {address, storageKeys} dicts. Default: [].

    Returns:
        Transaction dict ready for signing.
    """
    priority_fee = max_priority_fee_per_gas if max_priority_fee_per_gas is not None else _get_gas_price()
    fee_cap      = max_fee_per_gas          if max_fee_per_gas          is not None else _get_base_fee() + priority_fee

    return {
        "type":                 "0x2",
        "chainId":              config.chain_id,
        "nonce":                nonce if nonce is not None else _get_nonce(from_addr),
        "from":                 from_addr,
        "to":                   to_addr,
        "value":                value_wei,
        "gas":                  gas,
        "maxPriorityFeePerGas": priority_fee,
        "maxFeePerGas":         fee_cap,
        "data":                 data,
        "accessList":           access_list if access_list is not None else [],
    }


def build_type2_contract_deploy(
    from_addr:                str,
    bytecode:                 str,
    gas:                      int  = 3_000_000,
    max_priority_fee_per_gas: int  = None,
    max_fee_per_gas:          int  = None,
    nonce:                    int  = None,
    access_list:              list = None,
) -> dict:
    """Build a Type 0x2 EIP-1559 contract deployment transaction.

    No `to` field — its absence signals contract creation to the EVM.
    Do not set `value` unless the constructor is marked payable.

    Args:
        from_addr:                Deployer address (EIP-55 checksummed).
        bytecode:                 Compiled contract bytecode, 0x-prefixed hex string.
        gas:                      Gas limit. Default: 3_000_000.
        max_priority_fee_per_gas: Tip to validator in wei. Fetched if None.
        max_fee_per_gas:          Max total fee per gas in wei. Computed if None.
        nonce:                    Sender nonce. Fetched from node if None.
        access_list:              List of {address, storageKeys} dicts. Default: [].

    Returns:
        Transaction dict ready for signing.
    """
    priority_fee = max_priority_fee_per_gas if max_priority_fee_per_gas is not None else _get_gas_price()
    fee_cap      = max_fee_per_gas          if max_fee_per_gas          is not None else _get_base_fee() + priority_fee

    return {
        "type":                 "0x2",
        "chainId":              config.chain_id,
        "nonce":                nonce if nonce is not None else _get_nonce(from_addr),
        "from":                 from_addr,
        "data":                 bytecode,
        "gas":                  gas,
        "maxPriorityFeePerGas": priority_fee,
        "maxFeePerGas":         fee_cap,
        "accessList":           access_list if access_list is not None else [],
    }


def build_type2_contract_interaction(
    from_addr:                str,
    contract_addr:            str,
    signature:                str,
    params:                   str  = "",
    value_wei:                int  = 0,
    gas:                      int  = 100_000,
    max_priority_fee_per_gas: int  = None,
    max_fee_per_gas:          int  = None,
    nonce:                    int  = None,
    access_list:              list = None,
) -> dict:
    """Build a Type 0x2 EIP-1559 contract interaction transaction.

    Args:
        from_addr:                Caller address (EIP-55 checksummed).
        contract_addr:            Target contract address (EIP-55 checksummed).
        signature:                Canonical function signature e.g. 'transfer(address,uint256)'.
        params:                   ABI-encoded parameters as hex string (no 0x prefix). Default: ''.
        value_wei:                ETH to send in wei. Default: 0.
        gas:                      Gas limit. Default: 100_000.
        max_priority_fee_per_gas: Tip to validator in wei. Fetched if None.
        max_fee_per_gas:          Max total fee per gas in wei. Computed if None.
        nonce:                    Sender nonce. Fetched from node if None.
        access_list:              List of {address, storageKeys} dicts. Default: [].

    Returns:
        Transaction dict ready for signing.
    """
    priority_fee = max_priority_fee_per_gas if max_priority_fee_per_gas is not None else _get_gas_price()
    fee_cap      = max_fee_per_gas          if max_fee_per_gas          is not None else _get_base_fee() + priority_fee

    return {
        "type":                 "0x2",
        "chainId":              config.chain_id,
        "nonce":                nonce if nonce is not None else _get_nonce(from_addr),
        "from":                 from_addr,
        "to":                   contract_addr,
        "value":                value_wei,
        "gas":                  gas,
        "maxPriorityFeePerGas": priority_fee,
        "maxFeePerGas":         fee_cap,
        "data":                 "0x" + get_function_selector(signature).hex() + params,
        "accessList":           access_list if access_list is not None else [],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rpc = get_rpc_client()

    print("Chain ID  :", config.chain_id)
    print("Network   :", config.eth_network)
    print("Gas price :", _get_gas_price(), "wei")
    print("Base fee  :", _get_base_fee(),  "wei")


# ---------------------------------------------------------------------------
# Anvil usage examples
# Requires: anvil running on http://localhost:8545 (chain ID 31337)
# .env: ETH_RPC_ENDPOINT=http://localhost:8545 / ETH_NETWORK=anvil / ETH_CHAIN_ID=31337
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Setup — funded anvil accounts (default anvil addresses)
# ---------------------------------------------------------------------------
'''
rpc.call("anvil_mine",       ["0x10"])
rpc.call("anvil_reset",      [])
rpc.call("anvil_setBalance", ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "0x3635C9ADC5DEA00000"])
rpc.call("anvil_setBalance", ["0x70997970C51812dc3A010C7d01b50e0d17dc79C8", "0x3635C9ADC5DEA00000"])
'''

# ---------------------------------------------------------------------------
# Check balances
# ---------------------------------------------------------------------------
'''
for addr in [
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
]:
    wei = int(rpc.call("eth_getBalance", [addr, "latest"]), 16)
    print(f"{addr}  {wei} wei  ({wei / 10**18} ETH)")
'''

# ---------------------------------------------------------------------------
# Type 0x0 — ETH transfer
# ---------------------------------------------------------------------------
'''
tx = build_type0_eth_transfer(
    from_addr = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    to_addr   = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    value_wei = 10**18,  # 1 ETH
)
tx_hash    = rpc.call("eth_sendTransaction", [tx])
tx_receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
tx_obj     = rpc.call("eth_getTransactionByHash",  [tx_receipt["transactionHash"]])
print(tx_obj)
'''

# ---------------------------------------------------------------------------
# Type 0x0 — Contract deploy
# ---------------------------------------------------------------------------
'''
BYTECODE = "0x6080604052348015600e575f5ffd5b50335f5f6101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055506104368061005b5f395ff3fe608060405234801561000f575f5ffd5b506004361061003f575f3560e01c8063590791f214610043578063893d20e814610061578063a6f9dae11461007f575b5f5ffd5b61004b61009b565b6040516100589190610256565b60405180910390f35b6100696100d9565b60405161007691906102ae565b60405180910390f35b610099600480360381019061009491906102f5565b610100565b005b5f5f5f9054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1631905090565b5f5f5f9054906101000a900473ffffffffffffffffffffffffffffffffffffffff16905090565b5f5f9054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161461018e576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004016101859061037a565b60405180910390fd5b5f73ffffffffffffffffffffffffffffffffffffffff168173ffffffffffffffffffffffffffffffffffffffff16036101fc576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004016101f3906103e2565b60405180910390fd5b805f5f6101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b5f819050919050565b6102508161023e565b82525050565b5f6020820190506102695f830184610247565b92915050565b5f73ffffffffffffffffffffffffffffffffffffffff82169050919050565b5f6102988261026f565b9050919050565b6102a88161028e565b82525050565b5f6020820190506102c15f83018461029f565b92915050565b5f5ffd5b6102d48161028e565b81146102de575f5ffd5b50565b5f813590506102ef816102cb565b92915050565b5f6020828403121561030a576103096102c7565b5b5f610317848285016102e1565b91505092915050565b5f82825260208201905092915050565b7f4e6f7420746865206f776e6572000000000000000000000000000000000000005f82015250565b5f610364600d83610320565b915061036f82610330565b602082019050919050565b5f6020820190508181035f83015261039181610358565b9050919050565b7f496e76616c6964206164647265737300000000000000000000000000000000005f82015250565b5f6103cc600f83610320565b91506103d782610398565b602082019050919050565b5f6020820190508181035f8301526103f9816103c0565b905091905056fea2646970667358221220cc5d63358b8460c6700d728a6d14915e5eb1fa4777c60deb0796a1a2ffc7be1d64736f6c63430008210033"

tx = build_type0_contract_deploy(
    from_addr = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    bytecode  = BYTECODE,
    gas       = 3_000_000,
)
tx_hash       = rpc.call("eth_sendTransaction",      [tx])
tx_receipt    = rpc.call("eth_getTransactionReceipt", [tx_hash])
contract_addr = tx_receipt["contractAddress"]
print("Deployed at:", contract_addr)
# Read owner
print(rpc.call("eth_call", [{"to": contract_addr, "data": "0x893d20e8"}, "latest"]))
'''

# ---------------------------------------------------------------------------
# Type 0x0 — Contract interaction (changeOwner)
# ---------------------------------------------------------------------------
'''
tx = build_type0_contract_interaction(
    from_addr     = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    contract_addr = contract_addr,
    signature     = "changeOwner(address)",
    params        = "00000000000000000000000070997970c51812dc3a010c7d01b50e0d17dc79c8",
    gas           = 100_000,
)
tx_hash    = rpc.call("eth_sendTransaction",      [tx])
tx_receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
# Read updated owner
print(rpc.call("eth_call", [{"to": contract_addr, "data": "0x893d20e8"}, "latest"]))
'''

# ---------------------------------------------------------------------------
# Type 0x1 — ETH transfer
# ---------------------------------------------------------------------------
'''
tx = build_type1_eth_transfer(
    from_addr   = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    to_addr     = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    value_wei   = 10**18,  # 1 ETH
    access_list = [],
)
tx_hash    = rpc.call("eth_sendTransaction",      [tx])
tx_receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
tx_obj     = rpc.call("eth_getTransactionByHash",  [tx_receipt["transactionHash"]])
print(tx_obj)
'''

# ---------------------------------------------------------------------------
# Type 0x1 — Contract deploy
# ---------------------------------------------------------------------------
'''
tx = build_type1_contract_deploy(
    from_addr   = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    bytecode    = BYTECODE,
    gas         = 3_000_000,
    access_list = [],  # can include external contracts e.g. Uniswap, Aave
)
tx_hash       = rpc.call("eth_sendTransaction",      [tx])
tx_receipt    = rpc.call("eth_getTransactionReceipt", [tx_hash])
contract_addr = tx_receipt["contractAddress"]
print("Deployed at:", contract_addr)
print(rpc.call("eth_call", [{"to": contract_addr, "data": "0x893d20e8"}, "latest"]))
'''

# ---------------------------------------------------------------------------
# Type 0x1 — Contract interaction (changeOwner) with access list
# storageKeys: slot 0 = owner variable
# ---------------------------------------------------------------------------
'''
tx = build_type1_contract_interaction(
    from_addr     = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    contract_addr = contract_addr,
    signature     = "changeOwner(address)",
    params        = "00000000000000000000000070997970c51812dc3a010c7d01b50e0d17dc79c8",
    gas           = 100_000,
    access_list   = [
        {
            "address":     contract_addr,
            "storageKeys": [
                "0x0000000000000000000000000000000000000000000000000000000000000000",
            ]
        }
    ],
)
tx_hash    = rpc.call("eth_sendTransaction",      [tx])
tx_receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
print(rpc.call("eth_call", [{"to": contract_addr, "data": "0x893d20e8"}, "latest"]))
'''

# ---------------------------------------------------------------------------
# Type 0x2 — ETH transfer
# ---------------------------------------------------------------------------
'''
tx = build_type2_eth_transfer(
    from_addr = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    to_addr   = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    value_wei = 10**18,  # 1 ETH
)
tx_hash    = rpc.call("eth_sendTransaction",      [tx])
tx_receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
tx_obj     = rpc.call("eth_getTransactionByHash",  [tx_receipt["transactionHash"]])
print(tx_obj)
'''

# ---------------------------------------------------------------------------
# Type 0x2 — Contract deploy
# ---------------------------------------------------------------------------
'''
tx = build_type2_contract_deploy(
    from_addr   = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    bytecode    = BYTECODE,
    gas         = 500_000,
    access_list = [],  # can include external contracts e.g. Uniswap, Aave
)
tx_hash       = rpc.call("eth_sendTransaction",      [tx])
tx_receipt    = rpc.call("eth_getTransactionReceipt", [tx_hash])
contract_addr = tx_receipt["contractAddress"]
print("Deployed at:", contract_addr)
print(rpc.call("eth_call", [{"to": contract_addr, "data": "0x893d20e8"}, "latest"]))
'''

# ---------------------------------------------------------------------------
# Type 0x2 — Contract interaction (changeOwner) with access list
# ---------------------------------------------------------------------------
'''
tx = build_type2_contract_interaction(
    from_addr     = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    contract_addr = contract_addr,
    signature     = "changeOwner(address)",
    params        = "00000000000000000000000070997970c51812dc3a010c7d01b50e0d17dc79c8",
    gas           = 100_000,
    access_list   = [
        {
            "address":     contract_addr,
            "storageKeys": [
                "0x0000000000000000000000000000000000000000000000000000000000000000",
            ]
        }
    ],
)
tx_hash    = rpc.call("eth_sendTransaction",      [tx])
tx_receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
print(rpc.call("eth_call", [{"to": contract_addr, "data": "0x893d20e8"}, "latest"]))
'''