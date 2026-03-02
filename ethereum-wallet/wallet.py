"""
ethereum-wallet/wallet.py
=========================
From-scratch BIP-39/32/44 HD wallet implementation for Ethereum.

Standards implemented:
    BIP-39 — Mnemonic generation and seed derivation (chain agnostic)
    BIP-32 — HD key tree derivation (master key → child keys, chain agnostic)
    BIP-44 — Standardized multi-coin derivation paths:
              m / purpose' / coin_type' / account' / change / index
              Ethereum path: m / 44' / 60' / 0' / 0 / i

Key and address helpers (get_private_key, get_public_key, get_ethereum_address)
live in core/crypto.py and are imported from there — not redefined here.

NOTE on AES key/IV:
    The key and IV used here are hardcoded placeholders for demonstration.
    In production, derive the key from a user passphrase using PBKDF2,
    scrypt, or Argon2, and use a random IV per encryption.

Run directly:
    python3 wallet.py
"""

import os
import sys
import hmac
import hashlib
import struct
import base64

from pathlib import Path

from mnemonic import Mnemonic
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.crypto import get_private_key, get_public_key, get_ethereum_address


# ---------------------------------------------------------------------------
# BIP-39 — Mnemonic generation, encryption, storage, and seed derivation
# ---------------------------------------------------------------------------

def _generate_mnemonic() -> bytes:
    """Generate a random 256-bit BIP-39 mnemonic and return it as UTF-8 bytes."""
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(256)
    return mnemonic.encode("utf-8")


def _encrypt_mnemonic(mnemonic_bytes: bytes, key: bytes, iv: bytes) -> bytes:
    """Encrypt mnemonic bytes using AES-CBC."""
    aes_cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return aes_cipher.encrypt(pad(mnemonic_bytes, AES.block_size))


def _encode_mnemonic(encrypted_mnemonic_bytes: bytes) -> str:
    """Base64-encode encrypted mnemonic bytes to a storable string."""
    return base64.b64encode(encrypted_mnemonic_bytes).decode("utf-8")


def _create_mnemonic_file(encoded_encrypted_mnemonic: str, wallet_name: str) -> str:
    """Save the encoded encrypted mnemonic to a .wallet file under ./wallets/.

    Returns:
        The file path as a string.
    """
    directory = Path("./wallets")
    directory.mkdir(exist_ok=True)
    file_path = directory / f"{wallet_name}.wallet"
    file_path.write_text(encoded_encrypted_mnemonic)
    return str(file_path)


def _load_mnemonic(wallet_name: str) -> bytes:
    """Read the encoded encrypted mnemonic from a .wallet file.

    Returns:
        The encoded encrypted mnemonic as UTF-8 bytes.

    Raises:
        FileNotFoundError: If the wallet file does not exist.
    """
    file_path = Path("./wallets") / f"{wallet_name}.wallet"
    if not file_path.exists():
        raise FileNotFoundError(f"Wallet file '{file_path}' does not exist.")
    return file_path.read_text().encode("utf-8")


def _decode_mnemonic(encoded_encrypted_mnemonic_bytes: bytes) -> bytes:
    """Base64-decode the encoded mnemonic back to raw encrypted bytes."""
    return base64.b64decode(encoded_encrypted_mnemonic_bytes)


def _decrypt_mnemonic(encrypted_wallet_bytes: bytes, key: bytes, iv: bytes) -> str:
    """Decrypt AES-CBC encrypted mnemonic bytes and return the mnemonic string."""
    aes_cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    decrypted_data = unpad(aes_cipher.decrypt(encrypted_wallet_bytes), AES.block_size)
    return decrypted_data.decode("utf-8")


def _get_seed(mnemonic_text: str) -> bytes:
    """Derive a 512-bit BIP-39 seed from a mnemonic string."""
    mnemo = Mnemonic("english")
    return mnemo.to_seed(mnemonic_text)


class Bip_39:
    """High-level interface for BIP-39 wallet creation, loading, and deletion."""

    def create_wallet(self, wallet_name: str, key: bytes, iv: bytes) -> str:
        """Generate, encrypt, and save a new mnemonic wallet.

        Returns:
            The .wallet file path.
        """
        mnemonic_bytes = _generate_mnemonic()
        encrypted_mnemonic = _encrypt_mnemonic(mnemonic_bytes, key, iv)
        encoded_mnemonic = _encode_mnemonic(encrypted_mnemonic)
        return _create_mnemonic_file(encoded_mnemonic, wallet_name)

    def load_wallet(self, wallet_name: str, key: bytes, iv: bytes) -> str:
        """Load and decrypt an existing wallet.

        Returns:
            The mnemonic string.
        """
        encoded_mnemonic_bytes = _load_mnemonic(wallet_name)
        encrypted_mnemonic_bytes = _decode_mnemonic(encoded_mnemonic_bytes)
        return _decrypt_mnemonic(encrypted_mnemonic_bytes, key, iv)

    def get_seed(self, mnemonic_text: str) -> bytes:
        """Derive a BIP-39 seed from a mnemonic string."""
        return _get_seed(mnemonic_text)

    def delete_wallet(self, wallet_name: str) -> str:
        """Delete a wallet file.

        Returns:
            The deleted file path.

        Raises:
            FileNotFoundError: If the wallet does not exist.
        """
        file_path = Path("./wallets") / f"{wallet_name}.wallet"
        if not file_path.exists():
            raise FileNotFoundError(f"Wallet '{wallet_name}' does not exist.")
        file_path.unlink()
        return str(file_path)


# ---------------------------------------------------------------------------
# BIP-32 — HD key tree derivation from seed
# ---------------------------------------------------------------------------

# secp256k1 curve order — child keys must be within this range
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def _get_master_key(seed: bytes) -> tuple[bytes, bytes]:
    """Derive the BIP-32 master private key and chain code from a seed.

    Uses HMAC-SHA512 with the key "Bitcoin seed" as specified in BIP-32.

    Returns:
        (master_private_key, master_chain_code) as a tuple of bytes.
    """
    I = hmac.new(
        key=b"Bitcoin seed",
        msg=seed,
        digestmod=hashlib.sha512
    ).digest()
    return I[:32], I[32:]


def _get_child_key_normal(
    parent_private_key: bytes,
    parent_chain_code: bytes,
    index: int
) -> tuple[bytes, bytes]:
    """Derive a normal (non-hardened) child key.

    Index range: 0 to 2^31 - 1.

    Returns:
        (child_private_key, child_chain_code).
    """
    assert 0 <= index < HARDENED_OFFSET, f"Normal child index must be in range [0, 2^31-1], got {index}"
    data = get_public_key(get_private_key(parent_private_key)) + struct.pack(">L", index)
    I = hmac.new(parent_chain_code, data, hashlib.sha512).digest()
    IL, IR = I[:32], I[32:]
    child_int = (
        int.from_bytes(IL, "big") + int.from_bytes(parent_private_key, "big")
    ) % SECP256K1_N
    return child_int.to_bytes(32, "big"), IR


def _get_child_key_hardened(
    parent_private_key: bytes,
    parent_chain_code: bytes,
    index: int
) -> tuple[bytes, bytes]:
    """Derive a hardened child key.

    Index range: 2^31 to 2^32 - 1. More secure — not derivable from the
    parent public key.

    Returns:
        (child_private_key, child_chain_code).
    """
    data = b"\x00" + parent_private_key + struct.pack(">L", index)
    I = hmac.new(parent_chain_code, data, hashlib.sha512).digest()
    IL, IR = I[:32], I[32:]
    child_int = (
        int.from_bytes(IL, "big") + int.from_bytes(parent_private_key, "big")
    ) % SECP256K1_N
    return child_int.to_bytes(32, "big"), IR


class Bip_32:
    """High-level interface for BIP-32 master and child key derivation."""

    def get_master_key(self, seed: bytes) -> tuple[bytes, bytes]:
        """Derive master private key and chain code from a BIP-39 seed."""
        return _get_master_key(seed)

    def get_child_key(
        self,
        parent_private_key: bytes,
        parent_chain_code: bytes,
        index: int,
        hardened: bool = False
    ) -> tuple[bytes, bytes]:
        """Derive a child key.

        Args:
            hardened: Use hardened derivation if True. Default: False.

        Returns:
            (child_private_key, child_chain_code).
        """
        if hardened:
            return _get_child_key_hardened(parent_private_key, parent_chain_code, index)
        return _get_child_key_normal(parent_private_key, parent_chain_code, index)


# ---------------------------------------------------------------------------
# BIP-44 — Standardized multi-coin derivation paths
# ---------------------------------------------------------------------------

# Added to index to mark a hardened derivation step
HARDENED_OFFSET = 0x80000000


def _derive_eth_bip44_addresses(
    eth_master_priv: bytes,
    eth_master_chain_code: bytes,
    count: int
) -> list[list[bytes]]:
    """Derive `count` Ethereum child keys via BIP-44 path: m/44'/60'/0'/0/i.

    Returns:
        List of [private_key, chain_code] pairs, one per address index.
    """
    # m / 44'
    priv_44, chain_44 = _get_child_key_hardened(
        eth_master_priv, eth_master_chain_code, 44 + HARDENED_OFFSET
    )
    # m / 44' / 60'
    priv_44_60, chain_44_60 = _get_child_key_hardened(
        priv_44, chain_44, 60 + HARDENED_OFFSET
    )
    # m / 44' / 60' / 0'
    priv_44_60_0, chain_44_60_0 = _get_child_key_hardened(
        priv_44_60, chain_44_60, 0 + HARDENED_OFFSET
    )
    # m / 44' / 60' / 0' / 0  (external chain)
    priv_ext, chain_ext = _get_child_key_normal(priv_44_60_0, chain_44_60_0, 0)

    # m / 44' / 60' / 0' / 0 / i
    return [
        list(_get_child_key_normal(priv_ext, chain_ext, i))
        for i in range(count)
    ]


class Bip_44:
    """High-level interface for BIP-44 Ethereum address derivation."""

    def derive_ethereum_addresses(
        self,
        eth_master_priv: bytes,
        eth_master_chain_code: bytes,
        count: int
    ) -> list[list[bytes]]:
        """Derive `count` Ethereum child keys via BIP-44 path."""
        return _derive_eth_bip44_addresses(eth_master_priv, eth_master_chain_code, count)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Demonstrate the full BIP-39 → BIP-32 → BIP-44 → address workflow."""

    # NOTE: Replace with a securely derived key (PBKDF2/scrypt/Argon2) and
    # a random IV in any non-demo context.
    key = b"1234567890123456"
    iv  = b"1234567890123456"

    # --- BIP-39: load wallet and derive seed ---
    bip39 = Bip_39()

    # Uncomment to create or delete a wallet:
    # bip39.create_wallet("eth_main", key, iv)
    # bip39.delete_wallet("eth_main")

    eth_mnemonic = bip39.load_wallet("eth_main", key, iv)
    eth_seed     = bip39.get_seed(eth_mnemonic)

    # --- BIP-32: derive master key ---
    bip32 = Bip_32()
    eth_master_priv, eth_master_chain_code = bip32.get_master_key(eth_seed)

    # --- BIP-44: derive child addresses ---
    bip44 = Bip_44()
    eth_addresses = bip44.derive_ethereum_addresses(
        eth_master_priv, eth_master_chain_code, count=5
    )

    eth_priv_addr_0, _ = eth_addresses[0]
    eth_priv_addr_1, _ = eth_addresses[1]

    # --- Key → Address ---
    sender_priv    = get_private_key(eth_priv_addr_0)
    sender_pub     = get_public_key(sender_priv)
    sender_address = get_ethereum_address(sender_pub)

    receiver_priv    = get_private_key(eth_priv_addr_1)
    receiver_pub     = get_public_key(receiver_priv)
    receiver_address = get_ethereum_address(receiver_pub)

    print(f"Sender address:   {sender_address}")
    print(f"Receiver address: {receiver_address}")


if __name__ == "__main__":
    main()




