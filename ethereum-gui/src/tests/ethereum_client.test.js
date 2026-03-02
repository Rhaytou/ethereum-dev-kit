/**
 * ethereum-gui/src/tests/ethereum_client.test.js
 * ================================================
 * Unit tests for ethereum_client.js — RPC call construction and
 * convenience method routing. No node required. All network calls are mocked.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";


// ---------------------------------------------------------------------------
// Minimal inline EthereumRPC for isolated testing
// Mirrors the real class without the auth.js import dependency.
// ---------------------------------------------------------------------------

class EthereumRPC {
    constructor(endpoint, timeout = 30000) {
        this._url     = endpoint;
        this._timeout = timeout;
        this._headers = { "Content-Type": "application/json" };
    }

    async call(method, params = [], requestId = "ethereum-dev-kit") {
        const payload = { jsonrpc: "2.0", id: requestId, method, params };
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
        if (data.error != null) throw new Error(JSON.stringify(data.error));
        return data.result;
    }

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


// ---------------------------------------------------------------------------
// EthereumRPC.call — request construction
// ---------------------------------------------------------------------------

describe("EthereumRPC.call — request payload", () => {

    let fetchMock;

    beforeEach(() => {
        fetchMock = vi.fn().mockResolvedValue({
            ok:   true,
            json: async () => ({ result: "0x1", error: null }),
        });
        global.fetch = fetchMock;
    });

    it("sends POST to the endpoint", async () => {
        const rpc = new EthereumRPC("http://localhost:8545");
        await rpc.call("eth_blockNumber");
        expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8545");
        expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    });

    it("sets Content-Type application/json — no Authorization header", async () => {
        const rpc = new EthereumRPC("http://localhost:8545");
        await rpc.call("eth_blockNumber");
        const headers = fetchMock.mock.calls[0][1].headers;
        expect(headers["Content-Type"]).toBe("application/json");
        expect(headers["Authorization"]).toBeUndefined();
    });

    it("builds a valid JSON-RPC 2.0 payload", async () => {
        const rpc = new EthereumRPC("http://localhost:8545");
        await rpc.call("eth_chainId");
        const body = JSON.parse(fetchMock.mock.calls[0][1].body);
        expect(body.jsonrpc).toBe("2.0");
        expect(body.method).toBe("eth_chainId");
        expect(body.params).toEqual([]);
        expect(body.id).toBe("ethereum-dev-kit");
    });

    it("passes params correctly", async () => {
        const rpc = new EthereumRPC("http://localhost:8545");
        await rpc.call("eth_getBalance", ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "latest"]);
        const body = JSON.parse(fetchMock.mock.calls[0][1].body);
        expect(body.params).toEqual(["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "latest"]);
    });

    it("returns the result field", async () => {
        const rpc = new EthereumRPC("http://localhost:8545");
        const result = await rpc.call("eth_blockNumber");
        expect(result).toBe("0x1");
    });

    it("throws on HTTP error", async () => {
        fetchMock.mockResolvedValueOnce({ ok: false, status: 500, statusText: "Internal Server Error" });
        const rpc = new EthereumRPC("http://localhost:8545");
        await expect(rpc.call("eth_blockNumber")).rejects.toThrow("HTTP error: 500");
    });

    it("throws on RPC-level error", async () => {
        fetchMock.mockResolvedValueOnce({
            ok:   true,
            json: async () => ({ result: null, error: { code: -32601, message: "Method not found" } }),
        });
        const rpc = new EthereumRPC("http://localhost:8545");
        await expect(rpc.call("eth_unknown")).rejects.toThrow("Method not found");
    });

});


// ---------------------------------------------------------------------------
// Convenience shortcuts — each method calls the correct RPC method
// ---------------------------------------------------------------------------

describe("EthereumRPC — convenience shortcuts", () => {

    let rpc;

    beforeEach(() => {
        rpc = new EthereumRPC("http://localhost:8545");
        rpc.call = vi.fn().mockResolvedValue("0x0");
    });

    it("web3_clientVersion calls web3_clientVersion",  async () => { await rpc.web3_clientVersion();  expect(rpc.call).toHaveBeenCalledWith("web3_clientVersion"); });
    it("net_version calls net_version",                async () => { await rpc.net_version();         expect(rpc.call).toHaveBeenCalledWith("net_version"); });
    it("net_listening calls net_listening",            async () => { await rpc.net_listening();        expect(rpc.call).toHaveBeenCalledWith("net_listening"); });
    it("net_peerCount calls net_peerCount",            async () => { await rpc.net_peerCount();        expect(rpc.call).toHaveBeenCalledWith("net_peerCount"); });
    it("eth_protocolVersion calls eth_protocolVersion",async () => { await rpc.eth_protocolVersion();  expect(rpc.call).toHaveBeenCalledWith("eth_protocolVersion"); });
    it("eth_syncing calls eth_syncing",                async () => { await rpc.eth_syncing();          expect(rpc.call).toHaveBeenCalledWith("eth_syncing"); });
    it("eth_coinbase calls eth_coinbase",              async () => { await rpc.eth_coinbase();         expect(rpc.call).toHaveBeenCalledWith("eth_coinbase"); });
    it("eth_chainId calls eth_chainId",                async () => { await rpc.eth_chainId();          expect(rpc.call).toHaveBeenCalledWith("eth_chainId"); });
    it("eth_mining calls eth_mining",                  async () => { await rpc.eth_mining();           expect(rpc.call).toHaveBeenCalledWith("eth_mining"); });
    it("eth_hashrate calls eth_hashrate",              async () => { await rpc.eth_hashrate();         expect(rpc.call).toHaveBeenCalledWith("eth_hashrate"); });
    it("eth_gasPrice calls eth_gasPrice",              async () => { await rpc.eth_gasPrice();         expect(rpc.call).toHaveBeenCalledWith("eth_gasPrice"); });
    it("eth_accounts calls eth_accounts",              async () => { await rpc.eth_accounts();         expect(rpc.call).toHaveBeenCalledWith("eth_accounts"); });
    it("eth_blockNumber calls eth_blockNumber",        async () => { await rpc.eth_blockNumber();      expect(rpc.call).toHaveBeenCalledWith("eth_blockNumber"); });

});


// ---------------------------------------------------------------------------
// getMethods — registry completeness
// ---------------------------------------------------------------------------

describe("EthereumRPC.getMethods", () => {

    it("returns an object with all 13 methods", () => {
        const rpc     = new EthereumRPC("http://localhost:8545");
        const methods = rpc.getMethods();
        const expected = [
            "web3_clientVersion", "net_version", "net_listening", "net_peerCount",
            "eth_protocolVersion", "eth_syncing", "eth_coinbase", "eth_chainId",
            "eth_mining", "eth_hashrate", "eth_gasPrice", "eth_accounts", "eth_blockNumber",
        ];
        expected.forEach(name => expect(methods).toHaveProperty(name));
        expect(Object.keys(methods)).toHaveLength(13);
    });

    it("each entry is a function", () => {
        const rpc     = new EthereumRPC("http://localhost:8545");
        const methods = rpc.getMethods();
        Object.values(methods).forEach(fn => expect(typeof fn).toBe("function"));
    });

});









