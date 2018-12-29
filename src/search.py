import requests
import json
import time
from urllib.parse import parse_qs as pq
from neo4j.v1 import GraphDatabase
from constants import *

class Search: 
	def __init__(self, btcUrl, neo4j):
		self.btcUrl = btcUrl
		self.driver = GraphDatabase.driver(neo4j['url'], auth=(neo4j['user'], neo4j['pass']))

	def checkParams(self, environ):
		params = pq(environ['QUERY_STRING'])
		return 'addr' in params

	def getTxs(self, addrObj, maxTime, offset):
		url = self.btcUrl + addrObj['addr'] + '?&offset=' + str(offset)
		print('Checking ' + url)
		obj = (requests.get(url)).json()
		go  = True
		i   = 0
		with self.driver.session() as session:
				lastTxid = session.run("Match (a)-[r]->(b) WHERE a.addr = {addr} OR b.addr = {addr} "
							"RETURN r.txid ORDER BY r.epoch DESC LIMIT 1", addr = addrObj['addr'])
				lastTxid = lastTxid.single()
		if lastTxid is not None:
			lastTxid = lastTxid[0]
		for tx in obj['txs']:
			if time.time() - tx['time'] > maxTime or tx['hash'] == lastTxid:
				go = False
				break
			i = i + 1
			if i + offset > addrObj['n_txs']:
				go = False
			inputs  = {}
			outputs = {}
			amount  = None

			for inTx in tx['inputs']:
				if inTx['prev_out']['addr'] is not addrObj['addr']:
					for outTx in tx['out']:
						if 'addr' in outTx and outTx['addr'] == addrObj['addr']:
							total  = float(outTx['value'])
							change = 0.0

							for inTx in tx['inputs']:
								if inTx['prev_out']['addr'] == addrObj['addr']:
									change += float(inTx['prev_out']['value'])
								if inTx['prev_out']['addr'] in inputs:
									inputs[inTx['prev_out']['addr']] += (float(inTx['prev_out']['value'])/satoshi)
								else:
									inputs[inTx['prev_out']['addr']] =  (float(inTx['prev_out']['value'])/satoshi)
							amount = float((total - change)/satoshi)
							outputs[addrObj['addr']] = float(total/satoshi)
							break
					break
			if amount == None:
				total  = 0.0
				change = 0.0
				for inTx in tx['inputs']:
					if inTx['prev_out']['addr'] == addrObj['addr']:
						total += float(inTx['prev_out']['value'])
				for outTx in tx['out']:
					if 'addr' in outTx and outTx['addr'] == addrObj['addr']:
						change += float(outTx['value'])
					if 'addr' in outTx and outTx['addr'] in outputs:
						outputs[outTx['addr']] += (float(outTx['value'])/satoshi)
					elif 'addr' in outTx:
						outputs[outTx['addr']] =  (float(outTx['value'])/satoshi)
				amount = float((total - change)/satoshi)
				inputs[addrObj['addr']] = float(total/satoshi)
			
			if amount is not None and amount > addrObj['minTx']:
				with self.driver.session() as session:
					for inName, inValue in inputs.items():
						for outName, outValue in outputs.items():
							if inName == outName:
								continue
							val    = 0
							if inName == addrObj['addr'] and len(inputs) == 1:
								val = outValue
								relTxt = 'amountSent'
							else:
								val    = inValue
								relTxt = 'amountReceived'
							if val <= minVal:
								continue
							session.run("MERGE (a:Address {addr:$addr}) "
										"ON CREATE SET a.name = {addr}", addr = inName if inName is not addrObj['addr'] else outName)
							session.run("MATCH (a:Address), (b:Address) WHERE a.addr = {aAddr} AND b.addr = {bAddr} "
										"CREATE (a)-[:`" + str(val) + "` {txid:$txid, time:$time, " + relTxt + ":$val, txTotal:$amount, epoch:$epoch}]->(b)", txid = tx['hash'], 
										time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['time'])), epoch = tx['time'], relTxt = relTxt, val = str(val), aAddr = inName, bAddr = outName, amount = str(amount))
				addrObj['txs'].append({'txid': tx['hash'], 'time': tx['time'], 'inputs': inputs, 'outputs': outputs, 'amount': amount})
		if not go:
			print("All Transactions Collected")
			return addrObj
		else:
			return self.getTxs(addrObj, maxTime, offset + 50)

	def getAddr(self, environ):
		if not self.checkParams(environ):
			return "No Address"
		queryString = pq(environ["QUERY_STRING"])
		addr    = queryString['addr'][0]
		name	= queryString['name'][0] if 'name' in queryString and queryString['name'][0] is not '' else addr
		maxTime = int(queryString['time'][0]) if 'time' in queryString else None
		minTx	= float(queryString['minTx'][0]) if 'minTx' in queryString else -1
		obj = (requests.get(self.btcUrl + addr)).json()
		addrObj = {'name': name, 'addr': obj['address'], 'balance': obj['final_balance']/satoshi, 'n_txs': obj['n_tx'], 'minTx': minTx, 'txs': []}
		with self.driver.session() as session:
			session.run("MERGE (a:Address {addr:$addr}) "
						"ON CREATE SET a.minTx = {minTx}, a.name = {name} "
						"ON MATCH SET a.minTx  = {minTx}, a.name = {name}", name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'])
		if maxTime < 0 or maxTime is None: 
			return addrObj
		else:
			addrObj = self.getTxs(addrObj, maxTime, 0)
			return addrObj

	def close(self):
		self.driver.close()