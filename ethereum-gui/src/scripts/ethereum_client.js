/**
 * ethereum-gui/src/scripts/ethereum_client.js
 * =============================================
 * Browser-side JSON-RPC client for communicating with an Ethereum node.
 *
 * Endpoint is injected via auth.js, which reads from Vite env vars.
 * Ethereum nodes do not require HTTP Basic Auth — no credentials needed.
 *
 * Usage:
 *   import EthereumRPC from "./ethereum_client.js";
 *   import RPC_AUTH_ETH from "./auth.js";
 *
 *   const rpc = new EthereumRPC(RPC_AUTH_ETH.endpoint);
 *   const blockNumber = await rpc.eth_blockNumber();
 */

import RPC_AUTH_ETH from "./auth.js";

class EthereumRPC {
    /**
     * @param {string} endpoint - Full URL of the Ethereum node RPC endpoint.
     * @param {number} timeout  - Request timeout in milliseconds. Default: 30000.
     */
    constructor(endpoint, timeout = 30000) {
        this._url     = endpoint;
        this._timeout = timeout;
        this._headers = {
            "Content-Type": "application/json",
        };
    }

    /**
     * Send a JSON-RPC 2.0 request and return the result.
     *
     * @param {string} method    - Ethereum RPC method name.
     * @param {Array}  params    - Positional parameters. Default: [].
     * @param {string} requestId - Arbitrary ID echoed back by the node.
     * @returns {Promise<*>}     - The result field of the JSON-RPC response.
     * @throws {Error}           - On HTTP errors or RPC-level errors.
     */
    async call(method, params = [], requestId = "ethereum-dev-kit") {
        const payload = {
            jsonrpc: "2.0",
            id:      requestId,
            method,
            params,
        };

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this._timeout);

        let response;
        try {
            response = await fetch(this._url, {
                method:  "POST",
                headers: this._headers,
                body:    JSON.stringify(payload),
                signal:  controller.signal,
            });
        } finally {
            clearTimeout(timer);
        }

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error != null) {
            throw new Error(JSON.stringify(data.error));
        }

        return data.result;
    }

    // ------------------------------------------------------------------
    // Convenience shortcuts
    // ------------------------------------------------------------------

    async web3_clientVersion()  { return this.call("web3_clientVersion"); }
    async net_version()         { return this.call("net_version"); }
    async net_listening()       { return this.call("net_listening"); }
    async net_peerCount()       { return this.call("net_peerCount"); }
    async eth_protocolVersion() { return this.call("eth_protocolVersion"); }
    async eth_syncing()         { return this.call("eth_syncing"); }
    async eth_coinbase()        { return this.call("eth_coinbase"); }
    async eth_chainId()         { return this.call("eth_chainId"); }
    async eth_mining()          { return this.call("eth_mining"); }
    async eth_hashrate()        { return this.call("eth_hashrate"); }
    async eth_gasPrice()        { return this.call("eth_gasPrice"); }
    async eth_accounts()        { return this.call("eth_accounts"); }
    async eth_blockNumber()     { return this.call("eth_blockNumber"); }

    /**
     * Returns all built-in shortcut methods as callable entries.
     * Useful for dynamic dispatch in the dashboard.
     */
    getMethods() {
        return {
            web3_clientVersion:  () => this.web3_clientVersion(),
            net_version:         () => this.net_version(),
            net_listening:       () => this.net_listening(),
            net_peerCount:       () => this.net_peerCount(),
            eth_protocolVersion: () => this.eth_protocolVersion(),
            eth_syncing:         () => this.eth_syncing(),
            eth_coinbase:        () => this.eth_coinbase(),
            eth_chainId:         () => this.eth_chainId(),
            eth_mining:          () => this.eth_mining(),
            eth_hashrate:        () => this.eth_hashrate(),
            eth_gasPrice:        () => this.eth_gasPrice(),
            eth_accounts:        () => this.eth_accounts(),
            eth_blockNumber:     () => this.eth_blockNumber(),
        };
    }
}

export default EthereumRPC;




