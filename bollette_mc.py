import argparse
from mcrpc import RpcClient
from mcrpc.exceptions import RpcError

def create_bill(c,cliente,data,kwh,euro):
	res = c.liststreamkeyitems("cambio",cliente+"_"+data)
	if (len(res)>0):
		print("Bolletta già emessa")
		exit(-1)
	c.issuemore('1Sr2Q9zJPi8fEyophoNAsVV4yXmDU9LwBt1HZs','Kwh',kwh,0,{'Codice_cliente':cliente+"_"+data})
	euro_chain = kwh*euro
	c.issuemorefrom('1Sr2Q9zJPi8fEyophoNAsVV4yXmDU9LwBt1HZs','1JjwunoWz2a2JgsSjJY4i7y4kHGNNfUJtrhYYG','EURO',euro_chain,0,{'Codice_cliente':cliente+"_"+data})
	cod_ex = c.preparelockunspentfrom('1Sr2Q9zJPi8fEyophoNAsVV4yXmDU9LwBt1HZs',{'Kwh':kwh})
	long_code = c.createrawexchange(cod_ex['txid'],cod_ex['vout'],{'EURO':euro_chain})
	c.publish("cambio", cliente+"_"+data, long_code)
	return True

def pay_bill(c,cliente,data):
	res = c.liststreamkeyitems("cambio",cliente+"_"+data)
	if (len(res)==0):
		print("Bolletta non emessa")
		exit(-1)
	ask_value = c.decoderawexchange(res[0]["data"])["ask"]["assets"][0]["qty"]
	offer_value = c.decoderawexchange(res[0]["data"])["offer"]["assets"][0]["qty"]
	try:
		cod_ex = c.preparelockunspentfrom('1JjwunoWz2a2JgsSjJY4i7y4kHGNNfUJtrhYYG',{'EURO':ask_value})
	except RpcError:
		print("Bolletta già pagata")
		exit(-1)
	long_long_code = c._call("appendrawexchange", res[0]["data"],cod_ex['txid'],cod_ex['vout'],{'Kwh':offer_value})
	c.sendrawtransaction(long_long_code['hex'])
	return

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


c = RpcClient('127.0.0.1', '6726', 'multichainrpc', 'GeBtdxmPq4Qc7D24iSirviafUar85A6ohB62v4wAZ7h')
parser = argparse.ArgumentParser(description='Gestione delle bollette premarcate')
parser.add_argument('Azione', choices=['crea', 'paga','lista'],help='Azioni da compiere: creare una nuova bolletta, o conseguirne il pagamento')
parser.add_argument('Cliente',help='Identificativo del cliente')
parser.add_argument('Data',help='Mese di riferimento del bollettino MM/AAAA')
parser.add_argument('--Kwh', metavar='Kwh', type=float,help='Quantità in Kwh')
parser.add_argument('--EURO', metavar='EURO', type=float,help='Corrispettivo in euro')
args = parser.parse_args()
if (args.Azione=='crea'):
	if ((args.Kwh == None) or (args.EURO == None)):
		raise AssertionError("Parametri Kwh e Euro necessari")
	Kwh = float(args.Kwh)
	EURO = float(args.EURO)
	lc = create_bill(c,args.Cliente,args.Data,Kwh,EURO)
	print("Bollettino creato correttamente con identificativo: ",args.Cliente+"_"+args.Data)
elif (args.Azione=='paga'):
	pay_bill(c,args.Cliente,args.Data)
	print("Pagamento effettuato con successo")
else:
	unpayed_bill(c)
