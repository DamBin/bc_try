import argparse
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

@asyncio.coroutine
def create_bill(source,dest,loop,cliente,data,kwh,euro):
	res = [] #c.liststreamkeyitems("cambio",cliente+"_"+data)
	if (len(res)>0):
		print("Bolletta già emessa")
		exit(-1)
	euro_chain = kwh*euro
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
		to_script=output_script_dest,       # The issued coins are sent back to the same address
		change_script=output_script,        # The bitcoin change is sent back to the same address
		amount=int(round(euro_chain*100)))  # Issue euro_chain units of the asset
	str_meta = 'EURO_' + cliente + '_' + data
	transaction = builder.issue(issuance_parameters, metadata=str_meta.encode('utf-8'), fees=1000)
	send(rpc,transaction)

def pay_bill(source,dest,loop,cliente,data):
	bitcoin.SelectParams('testnet')
	rpc = bitcoin.rpc.Proxy('http://fuf:asdandari@localhost:18332')
	script_pub_key = rpc.validateaddress(source)["scriptPubKey"]
	output_script = bitcoin.core.x(script_pub_key)
	script_pub_key_dest = rpc.validateaddress(dest)["scriptPubKey"]
	output_script_dest = bitcoin.core.x(script_pub_key_dest)
	cache = openassets.protocol.OutputCache()
	transaction_provider = asyncio.coroutine(rpc.getrawtransaction)
	engine = openassets.protocol.ColoringEngine(transaction_provider, cache, loop)
	find = False
	unspent_outputs = []
	for output in listunspent(rpc):
		if output['scriptPubKey'] == output_script:
			transaction_hash = bitcoin.core.lx(output['txid'])
			output_index = output['outpoint'].n
			err = False
			try:
				colored_output = yield from engine.get_output(transaction_hash, output_index)
			except bitcoin.core.serialize.DeserializationExtraDataError:
				print("Un errore")
				err = True
			if ((colored_output.asset_id == None) or (err==True)):
				try:
					unspent_outputs.append(openassets.transactions.SpendableOutput(
						bitcoin.core.COutPoint(output['outpoint'].hash, output['outpoint'].n),
						(yield from engine.get_output(output['outpoint'].hash, output['outpoint'].n))
					))
				except bitcoin.core.serialize.DeserializationExtraDataError:
					pass
			else:
				output_index=1
				colored_output_meta = yield from engine.get_output(transaction_hash, output_index)
				if (colored_output_meta.script.find(b'EURO')!=-1):
					meta_out = colored_output_meta.script[colored_output_meta.script.find(b'EURO')+5:]
					str_cmp = (cliente+"_"+data).encode('utf-8')
					if (meta_out==str_cmp):
						find = True
						assetid = colored_output.asset_id
						unspent_outputs.append(openassets.transactions.SpendableOutput(
							bitcoin.core.COutPoint(output['outpoint'].hash, output['outpoint'].n),
							(yield from engine.get_output(output['outpoint'].hash, output['outpoint'].n))
							))
						asset_quantity = colored_output.asset_quantity
	if (find == False):
		print("Bolletta non emessa o già pagata")
		exit(-1)
	builder = openassets.transactions.TransactionBuilder(600)
	issuance_parameters = openassets.transactions.TransferParameters(
		unspent_outputs=unspent_outputs,    # Unspent outputs the coins are issued from
		to_script=output_script_dest,       # The issued coins are sent back to the same address
		change_script=output_script,        # The bitcoin change is sent back to the same address
		amount=asset_quantity)  # Issue euro_chain units of the asset
	transaction = builder.transfer_assets(assetid,issuance_parameters,output_script_dest,fees=1000)
#	send(rpc,transaction)

def listunspent(rpc):
        r = rpc._call('listunspent')
        r2 = []
        for unspent in r:
                unspent['outpoint'] = bitcoin.core.COutPoint(bitcoin.core.lx(unspent['txid']), unspent['vout'])
                unspent['txid']
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

def send(rpc,transaction):
        signed = rpc.signrawtransaction(transaction)
        txid = rpc.sendrawtransaction(signed['tx'])
        print(txid)

def unpayed_bill(c):
	res = c.listassets("EURO", verbose=True)
	printed = False
	for el in res[0]['issues']:
		if (el["issuers"][0]=='1JjwunoWz2a2JgsSjJY4i7y4kHGNNfUJtrhYYG'):
			print(el["details"]["Codice_cliente"])
			printed = True
	if (not printed):
		print("Tutte le bollette sono state pagate")
	return


parser = argparse.ArgumentParser(description='Gestione delle bollette premarcate')
parser.add_argument('Azione', choices=['crea', 'paga','lista'],help='Azioni da compiere: creare una nuova bolletta, o conseguirne il pagamento')
parser.add_argument('Cliente',help='Identificativo del cliente')
parser.add_argument('Data',help='Mese di riferimento del bollettino MM/AAAA')
parser.add_argument('--Kwh', metavar='Kwh', type=float,help='Quantità in Kwh')
parser.add_argument('--EURO', metavar='EURO', type=float,help='Corrispettivo in euro')
args = parser.parse_args()
loop = asyncio.get_event_loop()
source = "mwuaoGJvG1dvUeYEkeWzJQNmKdUxp5qmM1"
dest = "mtSHvdzTQGH5Yazkxnn1RBDChB5aCJkEUb"
if (args.Azione=='crea'):
	if ((args.Kwh == None) or (args.EURO == None)):
		raise AssertionError("Parametri Kwh e Euro necessari")
	Kwh = float(args.Kwh)
	EURO = float(args.EURO)
	loop.run_until_complete(create_bill(source,dest,loop,args.Cliente,args.Data,Kwh,EURO))
	print("Bollettino creato correttamente con identificativo: ",args.Cliente+"_"+args.Data)
elif (args.Azione=='paga'):
	loop.run_until_complete(pay_bill(dest,source,loop,args.Cliente,args.Data))
	print("Pagamento effettuato con successo")
else:
	unpayed_bill(c)
