import asyncio
import bitcoin.rpc
import openassets.protocol

@asyncio.coroutine
def main():
    bitcoin.SelectParams('testnet')

    # Create a RPC client for Bitcoin Core
    rpc_client = bitcoin.rpc.Proxy('http://fuf:asdandari@localhost:18332')
    # OutputCache implements the interface required for an output cache provider, but does not perform any caching
    cache = openassets.protocol.OutputCache()
    # The transaction provider is a function returning a transaction given its hash
    transaction_provider = asyncio.coroutine(rpc_client.getrawtransaction)
    # Instantiate the coloring engine
    coloring_engine = openassets.protocol.ColoringEngine(transaction_provider, cache, loop)

    transaction_hash = bitcoin.core.lx('4aeca58f49df33ed2bf53d52eee16dd107cd90919ef256dcef5b74c5fe3a8631')
    output_index = 0
    colored_output = yield from coloring_engine.get_output(transaction_hash, output_index)

    print(colored_output)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
