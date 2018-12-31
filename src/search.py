import requests
import json
import time
import pprint
from urllib.parse import parse_qs as pq
from neo4j.v1 import GraphDatabase
from constants import *
from traceback import print_exc

def numWithCommas(num):
	return ("{:,}".format(num))

class Search: 
	def __init__(self, btcUrl, usdtUrl, neo4j):
		self.btcUrl = btcUrl
		self.usdtUrl = usdtUrl
		self.driver = GraphDatabase.driver(neo4j['url'], auth=(neo4j['user'], neo4j['pass']))

	def checkParams(self, environ):
		params = pq(environ['QUERY_STRING'])
		return 'addr' in params

	def usdtRequest(self, addr, page):
		try: 
			proxy = proxies[0]
			if proxy['uses'] > 9:
				if time.time() - proxy['stopTime'] > 60:
					proxy['uses'] = 0
				else:
					del(proxies[0])
					proxies.append(proxy)
					return self.usdtRequest(addr, page)
			proxy = None if proxies[0]['proxy'] is None else proxies[0]['proxy']['https']
			print('Checking ' + addr + ' Page: ' + str(page), "Proxy: " + str(proxy))
			obj = (requests.post(self.usdtUrl, data = {'addr': addr, 'page': page}, proxies = proxies[0]['proxy'])).json()
			proxies[0]['uses'] = proxies[0]['uses'] + 1
			if proxies[0]['uses'] > 9:
				proxies[0]['stopTime'] = time.time()
			return obj
		except Exception as e:
			print(e)
			print_exc(file=open("log.txt", "a"))
			return {}

	def getTxs(self, addrObj, offset, isChange):
		url = self.btcUrl + addrObj['addr'] + '?&offset=' + str(offset)
		print('Checking ' + url)
		obj = (requests.get(url)).json()
		go  = True
		i   = 0
		lastTxid = ''
		if not isChange:
			with self.driver.session() as session:
					lastTxid = session.run("MATCH (a:BTC)-[r]->(b:BTC) WHERE a.addr = {addr} OR b.addr = {addr} "
											"RETURN r.txid ORDER BY r.epoch DESC LIMIT 1", addr = addrObj['addr'])
					lastTxid = lastTxid.single()
			if lastTxid is not None:
				lastTxid = lastTxid[0]
		for tx in obj['txs']:
			if time.time() - tx['time'] > int(addrObj['maxTime']) or tx['hash'] == lastTxid:
				if tx['hash'] == lastTxid:
					print("No New Transactions") 
				go = False
				break
			i = i + 1
			if i + offset > addrObj['n_txs']:
				go = False
			exist = self.driver.session().run("MATCH (a:BTC)-[r]->(b:BTC) WHERE r.txid = {txid} RETURN r.txid", txid = tx['hash'])
			exist = exist.single()
			if exist is not None:
				continue
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
							val = 0
							if inName == addrObj['addr'] and len(inputs) == 1:
								val = outValue
							else:
								val = inValue
							if val <= minVal:
								continue
							session.run("MERGE (a:BTC {addr:$addr}) "
										"ON CREATE SET a.name = {addr} "
										"RETURN a", addr = inName if outName == addrObj['addr'] else outName)
							session.run("MATCH (a:BTC), (b:BTC) WHERE a.addr = {aAddr} AND b.addr = {bAddr} "
										"CREATE (a)-[:`" + numWithCommas(float(val)) + "` {txid:$txid, time:$time, amount:$amount, epoch:$epoch, isTotal:$isTotal}]->(b)", txid = tx['hash'], 
										time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['time'])), epoch = tx['time'], aAddr = inName, bAddr = outName, amount = str(amount), isTotal = False)
				addrObj['txs'].append({'txid': tx['hash'], 'time': tx['time'], 'inputs': inputs, 'outputs': outputs, 'amount': amount})
		if not go:
			print("All Transactions Collected")
			return addrObj
		else:
			return self.getTxs(addrObj, offset + 50, isChange)

	def getUTxs(self, addrObj, page, isChange):
		obj = self.usdtRequest(addrObj['addr'], page)
		go  = True
		lastTxid = ''
		if not isChange:
			with self.driver.session() as session:
					lastTxid = session.run("Match (a:USDT)-[r]->(b:USDT) WHERE a.addr = {addr} OR b.addr = {addr} "
											"RETURN r.txid ORDER BY r.epoch DESC LIMIT 1", addr = addrObj['addr'])
					lastTxid = lastTxid.single()
			if lastTxid is not None:
				lastTxid = lastTxid[0]
		if 'transactions' in obj:
			for tx in obj['transactions']:
				if time.time() - tx['blocktime'] > addrObj['maxTime'] or tx['txid'] == lastTxid:
					if tx['txid'] == lastTxid:
						print("No New Transactions")
					go = False
					break
				exist = self.driver.session().run("MATCH (a:BTC)-[r]->(b:BTC) WHERE r.txid = {txid} RETURN r.txid", txid = tx['txid'])
				exist = exist.single()
				isValid = 'valid' not in tx or not tx['valid'] or int(tx['propertyid']) != 31 or (int(tx['type_int']) != 0 and int(tx['type_int']) != 55) or float(tx['amount']) < addrObj['minTx'] or exist is not None 
				if isValid:
					continue
				inName = tx['sendingaddress']
				outName = tx['referenceaddress']
				with self.driver.session() as session:
					session.run("MERGE (a:USDT {addr:$addr}) "
								"ON CREATE SET a.name = {addr}", addr = inName if outName == addrObj['addr'] else outName)
					session.run("MATCH (a:USDT), (b:USDT) WHERE a.addr = {aAddr} AND b.addr = {bAddr} "
								"CREATE (a)-[:`" + numWithCommas(float(tx['amount'])) + "` {txid:$txid, time:$time, amount:$amount, epoch:$epoch, isTotal:$isTotal}]->(b)",
								aAddr = inName, bAddr = outName, txid = tx['txid'], time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['blocktime'])), 
								amount = tx['amount'], epoch = tx['blocktime'], isTotal = False)
				addrObj['txs'].append({'txid': tx['txid'], 'time': tx['blocktime'], 'inputs': {inName: tx['amount']}, 'outputs': {outName: (float(tx['amount']) - float(tx['fee']))}, 'amount': tx['amount']})
		if obj == {} or not go or ('error' in obj and obj['error']) or page == obj['pages']:
			if not go:
				print("All Transactions Collected")
				return addrObj
			elif obj == {}:
				return self.getUTxs(addrObj, page, isChange)
			elif 'error' in obj and obj['error']:
				print("Max Transactions Requested From OmniExplorer")
				return self.getUTxs(addrObj, page, isChange)
			elif page == obj['pages']:
				print("No More Transactions Left")
				return addrObj
		else:
			return self.getUTxs(addrObj, page + 1, isChange)

	def getUSDT(self, environ):
		if not self.checkParams(environ):
			return "No Address"
		queryString = pq(environ["QUERY_STRING"])
		addr    = queryString['addr'][0]
		name	= queryString['name'][0] if 'name' in queryString and queryString['name'][0] is not '' else addr
		maxTime = int(queryString['time'][0]) if 'time' in queryString else -1
		minTx	= float(queryString['minTx'][0]) if 'minTx' in queryString else -1
		obj = self.usdtRequest(addr, 1)
		if obj is None:
			print("Address Does Not Exist")
			return "Address Does Not Exist"
		addrObj = {'name': name, 'addr': obj['address'], 'minTx': minTx, 'maxTime': maxTime, 'txs': []}
		isChange = False
		with self.driver.session() as session:
			result = session.run("MERGE (a:USDT {addr:$addr}) "
								"ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.maxTime = {maxTime} "
								"ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.maxTime = {maxTime} RETURN a.minTx", name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], maxTime = maxTime)
			result = result.single()
			isChange = True if result is not None else False
		if maxTime < 0 or maxTime is None: 
			return addrObj
		else:
			addrObj = self.getUTxs(addrObj, 1, isChange)
			return addrObj

	def refresh(self):
		with self.driver.session() as session:
			nodes = session.run("MATCH (n:BTC) RETURN n")
			if nodes is not None:
				for node in nodes:
					node = node.get(node.keys()[0])
					obj = (requests.get(self.btcUrl + node['addr'])).json()
					addrObj = { 'addr': obj['address'], 'balance': float(obj['final_balance']/satoshi)}
					session.run("MATCH (a:BTC) WHERE a.addr = {addr} "
								"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch}", addr = addrObj['addr'], balance = addrObj['balance'], lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
					if "minTx" in node and "maxTime" in node:
						addrObj = { 'addr': obj['address'], 'n_txs': obj['n_tx'], 'minTx': node['minTx'], 'maxTime': node['maxTime'], 'txs': []}
						addrObj = self.getTxs(addrObj, 0, False)
			nodes = session.run("MATCH (n:USDT) RETURN n")
			if nodes is not None:
				for node in nodes:
					node = node.get(node.keys()[0])
					obj = self.usdtRequest(node['addr'], 1)
					if 'error' in obj and obj['error']:
						return
					for coin in obj['balance']:
						if int(coin['id']) == 31:
							addrObj = { 'addr': obj['address'], 'balance': float(coin['value'])/satoshi}
							session.run("MATCH (a:USDT) WHERE a.addr = {addr} "
										"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch}", addr = addrObj['addr'], balance = addrObj['balance'], lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
							break
					if "minTx" in node and "maxTime" in node:
						addrObj = { 'addr': obj['address'], 'minTx': node['minTx'], 'maxTime': node['maxTime'], 'txs': []}
						addrObj = self.getUTxs(addrObj, 1, False)
			print("Addresses Updated")
			nodes = session.run("MATCH (a)-[r]->(b) WITH a, b, count(r) as rCount, SUM(toInt(r.amount)) as total " 
								"WHERE rCount > 4 RETURN a.addr, b.addr, total")
			if nodes is not None:
				for node in nodes:
					print(node)


	def getBTC(self, environ):
		if not self.checkParams(environ):
			return "No Address"
		queryString = pq(environ["QUERY_STRING"])
		addr    = queryString['addr'][0]
		name	= queryString['name'][0] if 'name' in queryString and queryString['name'][0] is not '' else addr
		maxTime = int(queryString['time'][0]) if 'time' in queryString else -1
		minTx	= float(queryString['minTx'][0]) if 'minTx' in queryString else -1
		obj = (requests.get(self.btcUrl + addr)).json()
		addrObj = {'name': name, 'addr': obj['address'], 'n_txs': obj['n_tx'], 'minTx': minTx, 'maxTime': maxTime, 'txs': []}
		isChange = False
		with self.driver.session() as session:
			result = session.run("MERGE (a:BTC {addr:$addr}) "
								"ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.maxTime = {maxTime} "
								"ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.maxTime = {maxTime} RETURN a.minTx", name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], maxTime = maxTime)
			result = result.single()
			isChange = True if result is not None else False
		if maxTime < 0 or maxTime is None: 
			return addrObj
		else:
			addrObj = self.getTxs(addrObj, 0, isChange)
			return addrObj

	def close(self):
		self.driver.close()