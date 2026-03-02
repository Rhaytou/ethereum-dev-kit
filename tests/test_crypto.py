"""
tests/test_crypto.py
====================
Unit tests for core/crypto.py — Ethereum cryptographic primitives.
No node required. All tests use deterministic inputs and known vectors.
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.crypto import (
    get_private_key,
    get_public_key,
    get_ethereum_address,
    keccak256,
    get_function_selector,
    get_event_topic,
)


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

KNOWN_PRIV_BYTES = bytes.fromhex(
    "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)  # anvil account 0 private key

def test_get_private_key_returns_private_key_object():
    from eth_keys import keys
    priv = get_private_key(KNOWN_PRIV_BYTES)
    assert isinstance(priv, keys.PrivateKey)

def test_get_private_key_deterministic():
    assert get_private_key(KNOWN_PRIV_BYTES) == get_private_key(KNOWN_PRIV_BYTES)

def test_get_public_key_returns_64_bytes():
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    assert len(pub) == 64

def test_get_public_key_deterministic():
    priv = get_private_key(KNOWN_PRIV_BYTES)
    assert get_public_key(priv) == get_public_key(priv)

def test_get_public_key_no_04_prefix():
    # Ethereum public keys are 64 bytes — no 0x04 uncompressed prefix
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    assert len(pub) == 64
    assert pub[0] != 0x04


# ---------------------------------------------------------------------------
# Address helpers
# ---------------------------------------------------------------------------

def test_get_ethereum_address_known_vector():
    # anvil account 0: priv → known address
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    addr = get_ethereum_address(pub)
    assert addr == "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

def test_get_ethereum_address_starts_with_0x():
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    addr = get_ethereum_address(pub)
    assert addr.startswith("0x")

def test_get_ethereum_address_is_42_chars():
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    addr = get_ethereum_address(pub)
    assert len(addr) == 42

def test_get_ethereum_address_is_checksummed():
    # EIP-55: mixed-case checksum — not all lower or all upper
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    addr = get_ethereum_address(pub)
    inner = addr[2:]  # strip 0x
    assert inner != inner.lower() or inner != inner.upper()

def test_get_ethereum_address_deterministic():
    priv = get_private_key(KNOWN_PRIV_BYTES)
    pub  = get_public_key(priv)
    assert get_ethereum_address(pub) == get_ethereum_address(pub)


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------

def test_keccak256_returns_32_bytes():
    assert len(keccak256(b"")) == 32

def test_keccak256_known_vector():
    # keccak256("") is a well-known constant
    result = keccak256(b"")
    assert result.hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

def test_keccak256_deterministic():
    assert keccak256(b"ethereum") == keccak256(b"ethereum")

def test_keccak256_different_inputs_differ():
    assert keccak256(b"a") != keccak256(b"b")


# ---------------------------------------------------------------------------
# ABI helpers — get_function_selector
# ---------------------------------------------------------------------------

def test_get_function_selector_returns_4_bytes():
    assert len(get_function_selector("transfer(address,uint256)")) == 4

def test_get_function_selector_known_vector():
    # ERC-20 transfer selector — well-known constant 0xa9059cbb
    result = get_function_selector("transfer(address,uint256)")
    assert result.hex() == "a9059cbb"

def test_get_function_selector_known_vector_balanceOf():
    # ERC-20 balanceOf selector — 0x70a08231
    result = get_function_selector("balanceOf(address)")
    assert result.hex() == "70a08231"

def test_get_function_selector_deterministic():
    sig = "transfer(address,uint256)"
    assert get_function_selector(sig) == get_function_selector(sig)

def test_get_function_selector_different_sigs_differ():
    assert get_function_selector("transfer(address,uint256)") != get_function_selector("approve(address,uint256)")


# ---------------------------------------------------------------------------
# ABI helpers — get_event_topic
# ---------------------------------------------------------------------------

def test_get_event_topic_returns_32_bytes():
    assert len(get_event_topic("Transfer(address,address,uint256)")) == 32

def test_get_event_topic_known_vector():
    # ERC-20 Transfer event topic — well-known constant
    result = get_event_topic("Transfer(address,address,uint256)")
    assert result.hex() == "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def test_get_event_topic_known_vector_approval():
    # ERC-20 Approval event topic — 0x8c5be1e5...
    result = get_event_topic("Approval(address,address,uint256)")
    assert result.hex() == "8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

def test_get_event_topic_deterministic():
    sig = "Transfer(address,address,uint256)"
    assert get_event_topic(sig) == get_event_topic(sig)

def test_get_event_topic_different_from_selector():
    sig = "Transfer(address,address,uint256)"
    assert get_event_topic(sig) != get_function_selector(sig)












