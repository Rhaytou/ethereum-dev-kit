# Ethereum Dev Kit

---

This project is a multi-chain developer kit built from the ground up, designed to give developers a complete, layered reference implementation of blockchain technology — from cryptographic primitives to a working GUI. It is not an application and not a tutorial. It is working code at every layer: node infrastructure, key derivation, raw transaction construction, RPC client, and interface. Each layer is intentionally minimal, documented, and runnable so a developer can read it, understand it, and extend it. The kit covers multiple blockchain networks — starting with Bitcoin, then Ethereum, then others — each implemented with the same depth and the same philosophy: no shortcuts, no library wrappers hiding the protocol, just the real thing at every level. The overall project is composed of multiple components, each living in its own repository: a Bitcoin dev kit, an Ethereum dev kit, and a unified multi-chain block explorer that grows as each chain is added. The spirit of the entire project is one coherent idea — that a developer should be able to clone it, run it, and have the full vertical stack of a blockchain network in front of them, from the lowest level to the interface.

---

## Stack

| Layer | Module | Technology |
|---|---|---|
| Node infrastructure | `ethereum-node` | Geth + Prysm + Nginx + Docker |
| Shared utilities | `core/` | Python — crypto, RPC, config |
| Key derivation | `ethereum-wallet` | Python — BIP-39, BIP-32, BIP-44 from scratch |
| RPC client | `ethereum-client` | Python — JSON-RPC over HTTP |
| Transaction construction | `ethereum-transactions` | Python — EIP-155, EIP-2930, EIP-1559 |
| Interface | `ethereum-gui` | React 19 + Vite |

---

## Architecture

```
ethereum-dev-kit/
├── ethereum-node/          Dockerized Geth + Prysm + Nginx load balancer
├── core/                   Shared crypto primitives, RPC factory, config
├── ethereum-wallet/        BIP-39/32/44 HD wallet — no external wallet lib
├── ethereum-client/        Python RPC client for the node
├── ethereum-transactions/  Raw transaction templates — Type 0x0, 0x1, 0x2
├── ethereum-gui/           React dashboard — block explorer, RPC runner
└── tests/                  Unit tests — no node required
```

All Python modules share a single virtual environment at the project root. `core/` is the shared foundation imported by every Python module.

---

## Prerequisites

- Docker + Docker Compose
- Python 3.10+
- Node.js 18+

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/Rhaytou/ethereum-dev-kit.git
cd ethereum-dev-kit
```

Copy and fill in the root environment file:
```bash
cp .env.example .env
```

Copy and fill in the GUI environment file:
```bash
cp ethereum-gui/.env.example ethereum-gui/.env
```

> Never commit `.env` files — they are gitignored by default.

---

### 2. Python environment

Set up once from the project root:

```bash
python3 -m venv envName
source envName/bin/activate
pip install -r requirements.txt
```

---

### 3. ethereum-node

Start the Geth + Prysm node and Nginx load balancer:

```bash
cd ethereum-node
make up
```

Verify the node is running:

```bash
# Through the load balancer
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
```

Available commands:
```bash
make up                # Start node + load balancer
make down              # Stop
make docker_clean_all  # Remove all Docker data
```

> For local development and testing, [Anvil](https://book.getfoundry.sh/anvil/) is the recommended alternative to running a full node. Set `ETH_RPC_ENDPOINT=http://localhost:8545` and `ETH_CHAIN_ID=31337` in your `.env`.

---

### 4. ethereum-wallet

BIP-39/32/44 HD wallet implemented from scratch — no external wallet library.

```bash
python3 ethereum-wallet/wallet.py
```

---

### 5. ethereum-client

Python JSON-RPC client. Requires a running node.

```bash
python3 ethereum-client/client.py
```

---

### 6. ethereum-transactions

Raw transaction construction. Requires a running node and a funded wallet.

```bash
python3 ethereum-transactions/tx_templates.py
```

Transaction types covered:

```
Type 0x0   Legacy (EIP-155)       fee = gas * gasPrice
Type 0x1   Access List (EIP-2930) fee = gas * gasPrice + access list
Type 0x2   Dynamic Fee (EIP-1559) fee ≤ gas * maxFeePerGas
```

Each type covers three use cases: EOA → EOA ETH transfer, contract deployment, contract interaction.

---

### 7. ethereum-gui

React 19 + Vite dashboard. Requires a running node and a populated `ethereum-gui/.env`.

```bash
cd ethereum-gui
npm install
npm run dev
```

---

### 8. Tests

Unit tests only — no node required. Covers `core/crypto`, `ethereum-wallet`, `ethereum-transactions`, and `ethereum-gui/src/scripts`.

**Python — from the project root with `envName` activated:**
```bash
pytest tests/
```

**JavaScript — from `ethereum-gui/`:**
```bash
npm test
```

---

## Environment Variables

**Root `.env`**
```
ETH_RPC_ENDPOINT=http://localhost:8001
ETH_NETWORK=sepolia
ETH_CHAIN_ID=11155111
```

**`ethereum-gui/.env`**
```
VITE_ETH_RPC_ENDPOINT=http://localhost:8001
```

---

## Run Order

```
ethereum-node  →  ethereum-wallet  →  ethereum-client  →  ethereum-transactions  →  ethereum-gui
```

Each layer depends on the one before it being available. You can run any layer in isolation — just be aware of what it expects.






