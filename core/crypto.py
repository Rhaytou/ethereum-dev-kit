"""
core/crypto.py
==============
Shared cryptographic primitives for the Ethereum Dev Kit.

This module centralises all low-level key, address, and hash functions.
Every module imports from here — nothing is redefined elsewhere.

Contents:
    Key helpers     — get_private_key, get_public_key
    Address helpers — get_ethereum_address
    Hash helpers    — keccak256
    ABI helpers     — get_function_selector, get_event_topic
"""

from eth_keys import keys
from eth_utils import keccak, to_checksum_address


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def get_private_key(priv_key_bytes: bytes) -> keys.PrivateKey:
    """Wrap raw private key bytes into an eth_keys PrivateKey object.

    Args:
        priv_key_bytes: 32-byte raw private key.

    Returns:
        An eth_keys PrivateKey instance.
    """
    return keys.PrivateKey(priv_key_bytes)


def get_public_key(priv_key: keys.PrivateKey) -> bytes:
    """Derive the uncompressed public key from a private key.

    Ethereum always uses uncompressed public keys (64 bytes, no 0x04 prefix).

    Args:
        priv_key: An eth_keys PrivateKey instance.

    Returns:
        64-byte uncompressed public key.
    """
    return priv_key.public_key.to_bytes()


# ---------------------------------------------------------------------------
# Address helpers
# ---------------------------------------------------------------------------

def get_ethereum_address(pubkey_bytes: bytes) -> str:
    """Derive a checksummed Ethereum address from a public key.

    Keccak-256 hashes the 64-byte public key, then takes the last 20 bytes
    as the address, returned in EIP-55 checksum format.

    Args:
        pubkey_bytes: 64-byte uncompressed public key (no 0x04 prefix).

    Returns:
        EIP-55 checksummed Ethereum address string (e.g. '0xAbCd...').
    """
    addr = keccak(pubkey_bytes)[-20:]
    return to_checksum_address(addr)


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------

def keccak256(data: bytes) -> bytes:
    """Apply Keccak-256 — standard Ethereum hashing primitive.

    Used for transaction hashing, address derivation, signature
    verification, and EVM storage slot computation.

    Args:
        data: Raw bytes to hash.

    Returns:
        32-byte Keccak-256 digest.
    """
    return keccak(data)


# ---------------------------------------------------------------------------
# ABI helpers
# ---------------------------------------------------------------------------

def get_function_selector(signature: str) -> bytes:
    """Derive the 4-byte ABI function selector from a function signature.

    The selector is the first 4 bytes of the Keccak-256 hash of the
    canonical function signature string.

    Args:
        signature: Canonical function signature, e.g.
                   'transfer(address,uint256)'

    Returns:
        4-byte function selector.

    Example:
        >>> get_function_selector('transfer(address,uint256)')
        b'\\xa9\\x05\\x9c\\xbb'
    """
    return keccak(signature.encode())[:4]


def get_event_topic(signature: str) -> bytes:
    """Derive the 32-byte topic hash from an event signature.

    The topic is the full Keccak-256 hash of the canonical event
    signature string. Used to identify events in transaction logs.

    Args:
        signature: Canonical event signature, e.g.
                   'Transfer(address,address,uint256)'

    Returns:
        32-byte event topic hash.

    Example:
        >>> get_event_topic('Transfer(address,address,uint256)').hex()
        'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    """
    return keccak(signature.encode())



