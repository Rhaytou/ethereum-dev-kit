/**
 * ethereum-gui/src/scripts/auth.js
 * =================================
 * RPC config for the Ethereum GUI.
 *
 * Ethereum nodes (Geth, Anvil, Sepolia) do not require HTTP Basic Auth.
 * Only the endpoint is read from Vite environment variables — never hardcoded.
 * Define the following in ethereum-gui/.env (gitignored):
 *
 *   VITE_ETH_RPC_ENDPOINT=http://localhost:8545
 *
 * Only variables prefixed with VITE_ are exposed to the browser bundle.
 * See ethereum-gui/.env.example for a safe template to commit.
 *
 * NOTE: For production deployments, RPC calls should be proxied through a
 * backend server so the node is never exposed directly to the client.
 * This approach (Vite env vars) is appropriate for local development only.
 */

const RPC_AUTH_ETH = {
    endpoint: import.meta.env.VITE_ETH_RPC_ENDPOINT ?? "http://localhost:8001",
};

if (!RPC_AUTH_ETH.endpoint) {
    throw new Error(
        "[ethereum-gui] Missing RPC endpoint.\n" +
        "Create ethereum-gui/.env with VITE_ETH_RPC_ENDPOINT.\n" +
        "Copy ethereum-gui/.env.example to get started."
    );
}

export default RPC_AUTH_ETH;