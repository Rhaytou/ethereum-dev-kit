import { useState, useMemo } from "react";
import './styles/ethereumblockexplorer.css';
import EthereumRPC from "../scripts/ethereum_client.js";
import RPC_AUTH_ETH from "../scripts/auth.js";

function EthereumBlockExplorer() {
    const RPC = useMemo(() => new EthereumRPC(RPC_AUTH_ETH.endpoint), []);
    const rpcMethods = useMemo(() => RPC.getMethods(), [RPC]);

    const [query, setQuery]                   = useState("");
    const [result, setResult]                 = useState(null);
    const [error, setError]                   = useState(null);
    const [loading, setLoading]               = useState(false);
    const [selectedMethod, setSelectedMethod] = useState("eth_blockNumber");

    // Reset output before each new call
    function reset() {
        setResult(null);
        setError(null);
    }

    // Detect query type and map to the correct RPC call
    // height: eth_getBlockByNumber -> {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x11", true],"id":1}
    // blockhash: eth_getBlockByHash -> {"jsonrpc":"2.0","method":"eth_getBlockByHash","params":["0x025b9ca4...", true],"id":1}
    // address: eth_getBalance -> {"jsonrpc":"2.0","method":"eth_getBalance","params":["0x407d73d8...", "latest"],"id":1}
    function detectAndCall(query) {
        const trimmed = query.trim();

        // Height: pure integer → convert to hex for eth_getBlockByNumber
        if (/^\d+$/.test(trimmed)) {
            return RPC.call("eth_getBlockByNumber", ["0x" + parseInt(trimmed).toString(16), true]);
        }

        // Block hash: 0x + 64 hex characters
        if (/^0x[0-9a-fA-F]{64}$/.test(trimmed)) {
            return RPC.call("eth_getBlockByHash", [trimmed, true]);
        }

        // Address: 0x + 40 hex characters
        if (/^0x[0-9a-fA-F]{40}$/.test(trimmed)) {
            return RPC.call("eth_getBalance", [trimmed, "latest"]);
        }

        // Fallback: pass raw to eth_getBalance
        return RPC.call("eth_getBalance", [trimmed, "latest"]);
    }

    async function handleSearch(e) {
        e.preventDefault();
        if (!query.trim()) return;
        reset();
        setLoading(true);
        try {
            const data = await detectAndCall(query);
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleMethod(e) {
        e.preventDefault();
        reset();
        setLoading(true);
        try {
            const data = await rpcMethods[selectedMethod]();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <section id="ethereumblockexplorer">
            <h2>Ethereum Block Explorer</h2>

            {/* Forms */}
            <section id="bbe-forms">

                {/* Search by block number / block hash / address */}
                <form className="bbe-form" onSubmit={handleSearch}>
                    <label htmlFor="bbe-search">Search</label>
                    <input
                        id="bbe-search"
                        type="text"
                        placeholder="Block number, block hash (0x…), address (0x…)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button type="submit">Search</button>
                </form>

                {/* Built-in RPC method runner */}
                <form className="bbe-form" onSubmit={handleMethod}>
                    <label htmlFor="bbe-method">RPC Method</label>
                    <select
                        id="bbe-method"
                        value={selectedMethod}
                        onChange={(e) => setSelectedMethod(e.target.value)}
                    >
                        {Object.keys(rpcMethods).map((m) => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                    <button type="submit">Run</button>
                </form>

            </section>

            {/* Result */}
            <section id="bbe-result">
                {loading && <p className="bbe-status">Loading…</p>}
                {error   && <p className="bbe-status bbe-error">{error}</p>}
                {result  && <pre>{JSON.stringify(result, null, 4)}</pre>}
            </section>

        </section>
    );
}

export default EthereumBlockExplorer;











