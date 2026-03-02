"""
tests/test_tx_templates.py
==========================
Unit tests for ethereum-transactions/tx_templates.py — dict structure only.
No node required. RPC calls are mocked.
"""

import sys
import pytest
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Mock core.config and core.rpc before importing tx_templates
# ---------------------------------------------------------------------------

mock_config        = MagicMock()
mock_config.chain_id   = 31337
mock_config.eth_network = "anvil"

sys.modules["core.config"] = MagicMock(config=mock_config)

mock_rpc_client = MagicMock()
mock_rpc_client.call.side_effect = lambda method, params: {
    "eth_gasPrice":          "0x3b9aca00",   # 1 gwei
    "eth_getBlockByNumber":  {"baseFeePerGas": "0x3b9aca00"},
    "eth_getTransactionCount": "0x0",
}.get(method, "0x0")

sys.modules["core.rpc"] = MagicMock(get_rpc_client=lambda: mock_rpc_client)

# core.crypto is real — selectors are tested directly
_spec = importlib.util.spec_from_file_location(
    "tx_templates",
    Path(__file__).resolve().parent.parent / "ethereum-transactions" / "tx_templates.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

build_type0_eth_transfer        = _mod.build_type0_eth_transfer
build_type0_contract_deploy     = _mod.build_type0_contract_deploy
build_type0_contract_interaction = _mod.build_type0_contract_interaction
build_type1_eth_transfer        = _mod.build_type1_eth_transfer
build_type1_contract_deploy     = _mod.build_type1_contract_deploy
build_type1_contract_interaction = _mod.build_type1_contract_interaction
build_type2_eth_transfer        = _mod.build_type2_eth_transfer
build_type2_contract_deploy     = _mod.build_type2_contract_deploy
build_type2_contract_interaction = _mod.build_type2_contract_interaction

FROM  = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TO    = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
BYTECODE = "0x6080"
SIG   = "transfer(address,uint256)"


# ---------------------------------------------------------------------------
# Type 0x0 — ETH transfer
# ---------------------------------------------------------------------------

def test_type0_eth_transfer_type():
    tx = build_type0_eth_transfer(FROM, TO, 10**18)
    assert tx["type"] == "0x0"

def test_type0_eth_transfer_chain_id():
    tx = build_type0_eth_transfer(FROM, TO, 10**18)
    assert tx["chainId"] == 31337

def test_type0_eth_transfer_required_keys():
    tx = build_type0_eth_transfer(FROM, TO, 10**18)
    for key in ["type", "chainId", "nonce", "from", "to", "value", "gas", "gasPrice", "data"]:
        assert key in tx

def test_type0_eth_transfer_no_access_list():
    tx = build_type0_eth_transfer(FROM, TO, 10**18)
    assert "accessList" not in tx

def test_type0_eth_transfer_value():
    tx = build_type0_eth_transfer(FROM, TO, 10**18)
    assert tx["value"] == 10**18

def test_type0_eth_transfer_explicit_gas():
    tx = build_type0_eth_transfer(FROM, TO, 10**18, gas=50_000)
    assert tx["gas"] == 50_000

def test_type0_eth_transfer_explicit_nonce():
    tx = build_type0_eth_transfer(FROM, TO, 10**18, nonce=5)
    assert tx["nonce"] == 5

def test_type0_eth_transfer_explicit_gas_price():
    tx = build_type0_eth_transfer(FROM, TO, 10**18, gas_price=2_000_000_000)
    assert tx["gasPrice"] == 2_000_000_000


# ---------------------------------------------------------------------------
# Type 0x0 — Contract deploy
# ---------------------------------------------------------------------------

def test_type0_contract_deploy_type():
    tx = build_type0_contract_deploy(FROM, BYTECODE)
    assert tx["type"] == "0x0"

def test_type0_contract_deploy_no_to():
    tx = build_type0_contract_deploy(FROM, BYTECODE)
    assert "to" not in tx

def test_type0_contract_deploy_no_value():
    tx = build_type0_contract_deploy(FROM, BYTECODE)
    assert "value" not in tx

def test_type0_contract_deploy_bytecode():
    tx = build_type0_contract_deploy(FROM, BYTECODE)
    assert tx["data"] == BYTECODE

def test_type0_contract_deploy_required_keys():
    tx = build_type0_contract_deploy(FROM, BYTECODE)
    for key in ["type", "chainId", "nonce", "from", "data", "gas", "gasPrice"]:
        assert key in tx


# ---------------------------------------------------------------------------
# Type 0x0 — Contract interaction
# ---------------------------------------------------------------------------

def test_type0_contract_interaction_type():
    tx = build_type0_contract_interaction(FROM, TO, SIG)
    assert tx["type"] == "0x0"

def test_type0_contract_interaction_has_to():
    tx = build_type0_contract_interaction(FROM, TO, SIG)
    assert tx["to"] == TO

def test_type0_contract_interaction_data_starts_with_selector():
    tx = build_type0_contract_interaction(FROM, TO, SIG)
    # transfer(address,uint256) selector = 0xa9059cbb
    assert tx["data"].startswith("0xa9059cbb")

def test_type0_contract_interaction_data_includes_params():
    params = "00" * 32
    tx = build_type0_contract_interaction(FROM, TO, SIG, params=params)
    assert tx["data"] == "0xa9059cbb" + params

def test_type0_contract_interaction_default_value_is_zero():
    tx = build_type0_contract_interaction(FROM, TO, SIG)
    assert tx["value"] == 0


# ---------------------------------------------------------------------------
# Type 0x1 — ETH transfer
# ---------------------------------------------------------------------------

def test_type1_eth_transfer_type():
    tx = build_type1_eth_transfer(FROM, TO, 10**18)
    assert tx["type"] == "0x1"

def test_type1_eth_transfer_has_access_list():
    tx = build_type1_eth_transfer(FROM, TO, 10**18)
    assert "accessList" in tx
    assert isinstance(tx["accessList"], list)

def test_type1_eth_transfer_default_access_list_empty():
    tx = build_type1_eth_transfer(FROM, TO, 10**18)
    assert tx["accessList"] == []

def test_type1_eth_transfer_custom_access_list():
    al = [{"address": TO, "storageKeys": []}]
    tx = build_type1_eth_transfer(FROM, TO, 10**18, access_list=al)
    assert tx["accessList"] == al

def test_type1_eth_transfer_required_keys():
    tx = build_type1_eth_transfer(FROM, TO, 10**18)
    for key in ["type", "chainId", "nonce", "from", "to", "value", "gas", "gasPrice", "data", "accessList"]:
        assert key in tx


# ---------------------------------------------------------------------------
# Type 0x1 — Contract deploy
# ---------------------------------------------------------------------------

def test_type1_contract_deploy_type():
    tx = build_type1_contract_deploy(FROM, BYTECODE)
    assert tx["type"] == "0x1"

def test_type1_contract_deploy_no_to():
    tx = build_type1_contract_deploy(FROM, BYTECODE)
    assert "to" not in tx

def test_type1_contract_deploy_has_access_list():
    tx = build_type1_contract_deploy(FROM, BYTECODE)
    assert "accessList" in tx


# ---------------------------------------------------------------------------
# Type 0x1 — Contract interaction
# ---------------------------------------------------------------------------

def test_type1_contract_interaction_type():
    tx = build_type1_contract_interaction(FROM, TO, SIG)
    assert tx["type"] == "0x1"

def test_type1_contract_interaction_selector():
    tx = build_type1_contract_interaction(FROM, TO, SIG)
    assert tx["data"].startswith("0xa9059cbb")

def test_type1_contract_interaction_has_access_list():
    tx = build_type1_contract_interaction(FROM, TO, SIG)
    assert "accessList" in tx


# ---------------------------------------------------------------------------
# Type 0x2 — ETH transfer
# ---------------------------------------------------------------------------

def test_type2_eth_transfer_type():
    tx = build_type2_eth_transfer(FROM, TO, 10**18)
    assert tx["type"] == "0x2"

def test_type2_eth_transfer_no_gas_price():
    tx = build_type2_eth_transfer(FROM, TO, 10**18)
    assert "gasPrice" not in tx

def test_type2_eth_transfer_has_max_fee_fields():
    tx = build_type2_eth_transfer(FROM, TO, 10**18)
    assert "maxPriorityFeePerGas" in tx
    assert "maxFeePerGas" in tx

def test_type2_eth_transfer_max_fee_gte_priority_fee():
    tx = build_type2_eth_transfer(FROM, TO, 10**18)
    assert tx["maxFeePerGas"] >= tx["maxPriorityFeePerGas"]

def test_type2_eth_transfer_explicit_fees():
    tx = build_type2_eth_transfer(FROM, TO, 10**18,
        max_priority_fee_per_gas=1_000_000_000,
        max_fee_per_gas=2_000_000_000,
    )
    assert tx["maxPriorityFeePerGas"] == 1_000_000_000
    assert tx["maxFeePerGas"]         == 2_000_000_000

def test_type2_eth_transfer_has_access_list():
    tx = build_type2_eth_transfer(FROM, TO, 10**18)
    assert "accessList" in tx

def test_type2_eth_transfer_required_keys():
    tx = build_type2_eth_transfer(FROM, TO, 10**18)
    for key in ["type", "chainId", "nonce", "from", "to", "value", "gas",
                "maxPriorityFeePerGas", "maxFeePerGas", "data", "accessList"]:
        assert key in tx


# ---------------------------------------------------------------------------
# Type 0x2 — Contract deploy
# ---------------------------------------------------------------------------

def test_type2_contract_deploy_type():
    tx = build_type2_contract_deploy(FROM, BYTECODE)
    assert tx["type"] == "0x2"

def test_type2_contract_deploy_no_to():
    tx = build_type2_contract_deploy(FROM, BYTECODE)
    assert "to" not in tx

def test_type2_contract_deploy_no_gas_price():
    tx = build_type2_contract_deploy(FROM, BYTECODE)
    assert "gasPrice" not in tx

def test_type2_contract_deploy_has_access_list():
    tx = build_type2_contract_deploy(FROM, BYTECODE)
    assert "accessList" in tx


# ---------------------------------------------------------------------------
# Type 0x2 — Contract interaction
# ---------------------------------------------------------------------------

def test_type2_contract_interaction_type():
    tx = build_type2_contract_interaction(FROM, TO, SIG)
    assert tx["type"] == "0x2"

def test_type2_contract_interaction_selector():
    tx = build_type2_contract_interaction(FROM, TO, SIG)
    assert tx["data"].startswith("0xa9059cbb")

def test_type2_contract_interaction_no_gas_price():
    tx = build_type2_contract_interaction(FROM, TO, SIG)
    assert "gasPrice" not in tx

def test_type2_contract_interaction_has_access_list():
    tx = build_type2_contract_interaction(FROM, TO, SIG)
    assert "accessList" in tx

def test_type2_contract_interaction_default_value_is_zero():
    tx = build_type2_contract_interaction(FROM, TO, SIG)
    assert tx["value"] == 0
















