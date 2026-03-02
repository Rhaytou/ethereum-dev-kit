"""
tests/test_wallet.py
====================
Unit tests for ethereum-wallet/wallet.py — BIP-32/39/44 derivation.
No node required. All tests use deterministic inputs and known vectors.
"""

import sys
import pytest
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "wallet_module",
    Path(__file__).resolve().parent.parent / "ethereum-wallet" / "wallet.py"
)
_wallet = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wallet)

_encrypt_mnemonic       = _wallet._encrypt_mnemonic
_decrypt_mnemonic       = _wallet._decrypt_mnemonic
_encode_mnemonic        = _wallet._encode_mnemonic
_decode_mnemonic        = _wallet._decode_mnemonic
_get_seed               = _wallet._get_seed
_get_master_key         = _wallet._get_master_key
_get_child_key_normal   = _wallet._get_child_key_normal
_get_child_key_hardened = _wallet._get_child_key_hardened
SECP256K1_N             = _wallet.SECP256K1_N
HARDENED_OFFSET         = _wallet.HARDENED_OFFSET


# ---------------------------------------------------------------------------
# BIP-39 — mnemonic encryption / decryption round-trip
# ---------------------------------------------------------------------------

KEY      = b"1234567890123456"  # 16-byte AES key
IV       = b"1234567890123456"  # 16-byte IV
MNEMONIC = b"abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

def test_encrypt_decrypt_roundtrip():
    encrypted = _encrypt_mnemonic(MNEMONIC, KEY, IV)
    decrypted = _decrypt_mnemonic(encrypted, KEY, IV)
    assert decrypted.encode("utf-8") == MNEMONIC

def test_encode_decode_roundtrip():
    encrypted = _encrypt_mnemonic(MNEMONIC, KEY, IV)
    encoded   = _encode_mnemonic(encrypted)
    decoded   = _decode_mnemonic(encoded.encode("utf-8"))
    assert decoded == encrypted

def test_encryption_is_deterministic():
    enc1 = _encrypt_mnemonic(MNEMONIC, KEY, IV)
    enc2 = _encrypt_mnemonic(MNEMONIC, KEY, IV)
    assert enc1 == enc2

def test_wrong_key_fails_decryption():
    encrypted = _encrypt_mnemonic(MNEMONIC, KEY, IV)
    wrong_key = b"wrongkey12345678"
    with pytest.raises(Exception):
        _decrypt_mnemonic(encrypted, wrong_key, IV)


# ---------------------------------------------------------------------------
# BIP-39 — seed derivation
# ---------------------------------------------------------------------------

def test_get_seed_returns_64_bytes():
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    seed = _get_seed(mnemonic)
    assert len(seed) == 64

def test_get_seed_deterministic():
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    assert _get_seed(mnemonic) == _get_seed(mnemonic)

def test_get_seed_known_vector():
    # BIP-39 test vector — no passphrase
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    seed = _get_seed(mnemonic)
    assert seed.hex().startswith("5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1")


# ---------------------------------------------------------------------------
# BIP-32 — master key derivation
# ---------------------------------------------------------------------------

def test_master_key_returns_two_32_byte_values():
    seed = bytes.fromhex("5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1" * 2)
    priv, chain = _get_master_key(seed)
    assert len(priv) == 32
    assert len(chain) == 32

def test_master_key_deterministic():
    seed = b"\x00" * 64
    assert _get_master_key(seed) == _get_master_key(seed)

def test_master_key_known_vector():
    # BIP-32 test vector 1 — same seed phrase used for both Bitcoin and Ethereum
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    priv, chain = _get_master_key(seed)
    assert priv.hex()  == "e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35"
    assert chain.hex() == "873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508"


# ---------------------------------------------------------------------------
# BIP-32 — child key derivation
# ---------------------------------------------------------------------------

def test_normal_child_key_length():
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    priv, chain = _get_master_key(seed)
    child_priv, child_chain = _get_child_key_normal(priv, chain, 0)
    assert len(child_priv) == 32
    assert len(child_chain) == 32

def test_hardened_child_key_length():
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    priv, chain = _get_master_key(seed)
    child_priv, child_chain = _get_child_key_hardened(priv, chain, HARDENED_OFFSET)
    assert len(child_priv) == 32
    assert len(child_chain) == 32

def test_child_key_within_curve_order():
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    priv, chain = _get_master_key(seed)
    child_priv, _ = _get_child_key_normal(priv, chain, 0)
    assert int.from_bytes(child_priv, "big") < SECP256K1_N

def test_normal_and_hardened_differ():
    seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    priv, chain = _get_master_key(seed)
    normal   = _get_child_key_normal(priv, chain, 0)
    hardened = _get_child_key_hardened(priv, chain, HARDENED_OFFSET)
    assert normal != hardened














