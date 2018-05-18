from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret
import asyncio
import bitcoin.rpc
import openassets.protocol
import openassets.transactions
import binascii
from bitcoin.core import b2x,COutPoint,lx,COIN,Hash160,CMutableTransaction
from bitcoin.core.script import CScript,SIGHASH_NONE, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
import six
from bitcoin.core import *

unhexlify = lambda h: binascii.unhexlify(h.encode('utf8'))

def listunspent(rpc):
	r = rpc._call('listunspent')
	r2 = []
	for unspent in r:
		unspent['outpoint'] = bitcoin.core.COutPoint(bitcoin.core.lx(unspent['txid']), unspent['vout'])
		del unspent['txid']
		del unspent['vout']
		# address isn't always available as Bitcoin Core allows scripts w/o
		# an address type to be imported into the wallet, e.g. non-p2sh
		# segwit
		try:
			unspent['address'] = CBitcoinAddress(unspent['address'])
		except KeyError:
			pass
		unspent['scriptPubKey'] = bitcoin.core.CScript(unhexlify(unspent['scriptPubKey']))
		unspent['amount'] = int(unspent['amount'] * COIN)
		r2.append(unspent)
	return r2

@asyncio.coroutine
def main(source,dest,loop):
	bitcoin.SelectParams('testnet')
	rpc = bitcoin.rpc.Proxy('http://fuf:asdandari@localhost:18332')
	script_pub_key = rpc.validateaddress(source)["scriptPubKey"]
	output_script = bitcoin.core.x(script_pub_key)
	script_pub_key_dest = rpc.validateaddress(dest)["scriptPubKey"]
	output_script_dest = bitcoin.core.x(script_pub_key_dest)
	transaction_provider = asyncio.coroutine(rpc.getrawtransaction)
	engine = openassets.protocol.ColoringEngine(transaction_provider, openassets.protocol.OutputCache(), loop)
	unspent_outputs = []
	am = 0
	for output in listunspent(rpc):
		if output['scriptPubKey'] == output_script:
			unspent_outputs.append(openassets.transactions.SpendableOutput(
				bitcoin.core.COutPoint(output['outpoint'].hash, output['outpoint'].n),
				(yield from engine.get_output(output['outpoint'].hash, output['outpoint'].n))
				))
			am += output['amount']
	builder = openassets.transactions.TransactionBuilder(600)
	issuance_parameters = openassets.transactions.TransferParameters(
		unspent_outputs=unspent_outputs,    # Unspent outputs the coins are issued from
		to_script=output_script_dest,            # The issued coins are sent back to the same address
		change_script=output_script,        # The bitcoin change is sent back to the same address
		amount=1)                          # Issue 1,500 units of the asset
	transaction = builder.issue(issuance_parameters, metadata=b'Gianpiero_07/2018', fees=1000)
	send(rpc,transaction)

def send(rpc,transaction):
	signed = rpc.signrawtransaction(transaction)
	txid = rpc.sendrawtransaction(signed['tx'])
	print(txid)

loop = asyncio.get_event_loop()
source = "mz5YgXbD3UHV8kRN29ftwkyyQMw5JSTVJE"
dest = "mtSHvdzTQGH5Yazkxnn1RBDChB5aCJkEUb"
loop.run_until_complete(main(source,dest,loop))

