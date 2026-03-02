"""
core/config.py
==============
Central configuration loader for the Ethereum Dev Kit.

Reads all environment variables from the project root .env file using
python-dotenv. Every module in the project imports from here — no
credentials or config values are ever hardcoded anywhere else.

Usage:
    from core.config import config

    print(config.rpc_endpoint)
    print(config.eth_network)
    print(config.chain_id)
"""

import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Load .env from the project root (two levels up from this file)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_FILE)


# ---------------------------------------------------------------------------
# Config dataclass — typed, explicit, IDE-friendly
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Config:
    """Immutable configuration object built from environment variables."""

    rpc_endpoint: str
    eth_network:  str
    chain_id:     int

    @classmethod
    def from_env(cls) -> "Config":
        """Build a Config instance from environment variables.

        Raises:
            EnvironmentError: If any required variable is missing.
        """
        missing = []

        rpc_endpoint = os.getenv("ETH_RPC_ENDPOINT")
        eth_network  = os.getenv("ETH_NETWORK",  "anvil") # (ETH_NETWORK: sepolia / ETH_CHAIN_ID: 11155111) (ETH_NETWORK: anvil / ETH_CHAIN_ID: 31337)
        chain_id_raw = os.getenv("ETH_CHAIN_ID", "31337")

        if not rpc_endpoint:
            missing.append("ETH_RPC_ENDPOINT")

        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Make sure your .env file exists at: {_ENV_FILE}\n"
                f"You can copy .env.example to .env to get started."
            )

        return cls(
            rpc_endpoint=rpc_endpoint,
            eth_network=eth_network,
            chain_id=int(chain_id_raw),
        )


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
config = Config.from_env()





