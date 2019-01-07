import requests
import json
import time
import pprint
from urllib.parse import parse_qs as pq
from neo4j.v1 import GraphDatabase
from constants import *
from traceback import print_exc
from threading import Thread, Lock
import queue

def numWithCommas(num):
	return ("{:,}".format(num))

class Search: 
	def __init__(self, btcUrl, usdtUrl, neo4j):
		self.btcUrl = btcUrl
		self.usdtUrl = usdtUrl
		self.driver = GraphDatabase.driver(neo4j['url'], auth=(neo4j['user'], neo4j['pass']))
		self.mutex = Lock()
		self.done = False
		self.queue = queue.Queue()
		self.page = 0
		self.addrObj = {}

	def checkParams(self, environ):
		params = pq(environ['QUERY_STRING'])
		return 'addr' in params

	def usdtRequest(self, addr, page, num):
		try: 
			proxy = 'None' if proxies[num] is None else str(proxies[num]['https'])
			print('Checking ' + addr + ' Page: ' + str(page), "Proxy: " + proxy)
			obj = (requests.post(self.usdtUrl, data = {'addr': addr, 'page': page}, proxies = proxies[num])).json()
			return obj
		except Exception as e:
			print(e)
			print_exc(file=open("log.txt", "a"))
			return None

	def getTxs(self, threadNum, addrObj, lastTxid):
		while not self.done:
			offset = 0
			self.mutex.acquire()
			offset = self.page
			self.page += 50
			self.mutex.release()
			print("Offset {} with Thread {}".format(offset, threadNum))
			url = self.btcUrl + addrObj['addr'] + '?&offset=' + str(offset)
			print('Checking ' + url)
			obj = (requests.get(url)).json()
			if len(obj['txs']) == 0:
				print("No More Transactions Left")
				self.mutex.acquire()
				self.done = True
				self.mutex.release()
				return 0
			i = 0
			for tx in obj['txs']:
				if time.time() - tx['time'] > int(addrObj['maxTime']) or tx['hash'] == lastTxid:
					if tx['hash'] == lastTxid:
						print("No New Transactions") 
					self.mutex.acquire()
					self.done = True
					self.mutex.release()
					break
				i += 1	
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
				if amount is None:
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
					sortedTx = {'addr': addrObj['addr'], 'txid': tx['hash'], 'time': tx['time'], 'inputs': inputs, 'outputs': outputs, 'amount': amount}
					self.queue.put(sortedTx)
			if self.done:
				print("All Transactions Collected for thread {}".format(threadNum))
				return 0
		return 0

	def getUTxs(self, threadNum, addrObj, lastTxid):
		while not self.done:
			currPage = 1
			self.mutex.acquire()
			currPage = self.page
			self.page += 1
			self.mutex.release()
			print("Page {} with Thread {}".format(currPage, threadNum))
			obj = self.usdtRequest(addrObj['addr'], currPage, threadNum)
			#add to queue
			if obj is None or ('error' in obj and obj['error']):
				if obj is None or 'error' in obj and obj['error']  :
					print("Max Transactions Requested From OmniExplorer")
					#wait
					starttime = time.time()
					wait = True
					while wait:
						print("Waiting on Thread {}".format(threadNum))
						time.sleep(60.0 - ((time.time() - starttime) % 60.0))
						wait = False
						obj = self.usdtRequest(addrObj['addr'], currPage, threadNum)
			for tx in obj['transactions']:
				if time.time() - tx['blocktime'] > addrObj['maxTime'] or tx['txid'] == lastTxid:
					if tx['txid'] == lastTxid:
						print("No New Transactions")
					self.mutex.acquire()
					self.done = True
					self.mutex.release()
					break
				exist = self.driver.session().run("MATCH (a:USDT)-[r]->(b:USDT) WHERE r.txid = {txid} RETURN r.txid", txid = tx['txid'])
				exist = exist.single()
				isNotValid = 'valid' not in tx or not tx['valid'] or int(tx['propertyid']) != 31 or (int(tx['type_int']) != 0 and int(tx['type_int']) != 55) or float(tx['amount']) < addrObj['minTx'] or exist is not None 
				if isNotValid:
					continue
				inName = tx['sendingaddress']
				outName = tx['referenceaddress']
				sortedTx = {'addr': addrObj['addr'], 'txid': tx['txid'], 'time': tx['blocktime'], 'inputs': {inName: float(tx['amount'])}, 'outputs': {outName: (float(tx['amount']) - float(tx['fee']))}, 'amount': tx['amount']}
				#print("Here {}".format(sortedTx['txid']))
				self.queue.put(sortedTx)
			if self.page == obj['pages']:
				print("No More Transactions Left")
				self.mutex.acquire()
				self.done = True
				self.mutex.release()
			if self.done:
				print("All Transactions Collected for thread {}".format(threadNum))
				return 0
		return 0

	def databaseThread(self, addrObj):
		tx = self.queue.get(block = True, timeout = None)
		if tx is not None:
			self.addrObj['txs'].append(tx)
		while tx:
			for inName, inValue in tx['inputs'].items():
				for outName, outValue in tx['outputs'].items():
					if inName == outName:
						continue
					val = 0
					if inName == tx['addr'] and len(tx['inputs']) == 1:
						val = outValue
					else:
						val = inValue
					if float(val) <= minVal:
						continue
					with self.driver.session() as session:
						session.run("MERGE (a:" + addrObj['type'] + " {addr:$addr}) "
									"ON CREATE SET a.name = {addr}", addr = inName if outName == tx['addr'] else outName)
						session.run("MATCH (a:" + addrObj['type'] + "), (b:" + addrObj['type'] + ") WHERE a.addr = {aAddr} AND b.addr = {bAddr} "
									"CREATE (a)-[:`" + numWithCommas(float(val)) + "` {txid:$txid, time:$time, amount:$amount, epoch:$epoch, isTotal:$isTotal}]->(b)",
									aAddr = inName, bAddr = outName, txid = tx['txid'], time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['time'])), 
									amount = tx['amount'], epoch = tx['time'], isTotal = False)
			tx = self.queue.get(block=True, timeout=None)
			if tx is not None:
				self.addrObj['txs'].append(tx)
		pprint.pprint(self.addrObj)
		return 0

	def getUSDT(self, environ):
		if not self.checkParams(environ):
			return "No Address"
		queryString = pq(environ["QUERY_STRING"])
		addr    = queryString['addr'][0]
		name	= queryString['name'][0] if 'name' in queryString and queryString['name'][0] is not '' else addr
		maxTime = int(queryString['time'][0]) if 'time' in queryString else -1
		minTx	= float(queryString['minTx'][0]) if 'minTx' in queryString else -1
		obj = self.usdtRequest(addr, 1, 0)
		if obj is None:
			print("Address Does Not Exist")
			return "Error Getting {}".format(addr)
		addrObj = {'name': name, 'type': 'USDT', 'addr': obj['address'], 'minTx': minTx, 'maxTime': maxTime, 'txs': []}
		self.addrObj = addrObj
		with self.driver.session() as session:
			session.run("MERGE (a:USDT {addr:$addr}) "
						"ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.maxTime = {maxTime} "
						"ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.maxTime = {maxTime}", name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], maxTime = maxTime)
		if maxTime < 0 or maxTime is None: 
			return addrObj
		else:
			return self.threadsUSDT(addrObj, )

	def threadsUSDT(self, addrObj):
		self.done = False
		self.page = 1
		threads = []
		with self.driver.session() as session:
			lastTxid = session.run("Match (a:USDT)-[r]->(b:USDT) WHERE (a.addr = {addr} OR b.addr = {addr}) AND NOT r.isTotal "
									"RETURN r.txid ORDER BY r.epoch DESC LIMIT 1", addr = addrObj['addr'])
			lastTxid = lastTxid.single()
		if lastTxid is not None:
			lastTxid = lastTxid[0]
		else:
			lastTxid = '' 
		print(lastTxid)
		try:
			dataThread = Thread(target=self.databaseThread, args=(addrObj, ))
			dataThread.start()
		except Exception as e:
			print(e)
			print_exc(file=open("log.txt", "a"))
		for x in range(0, len(proxies)):
			threads.append(Thread(target=self.getUTxs, args = (x, addrObj, lastTxid)))
			threads[x].start()
		for x in range(0, len(proxies)):
			threads[x].join()
		self.queue.put(None)
		dataThread.join()
		print("Done with all Threads")
		return str(self.addrObj)

	def getBTC(self, environ):
		if not self.checkParams(environ):
			return "No Address"
		queryString = pq(environ["QUERY_STRING"])
		addr    = queryString['addr'][0]
		name	= queryString['name'][0] if 'name' in queryString and queryString['name'][0] is not '' else addr
		maxTime = int(queryString['time'][0]) if 'time' in queryString else -1
		minTx	= float(queryString['minTx'][0]) if 'minTx' in queryString else -1
		obj = None
		try: 
			obj = (requests.get(self.btcUrl + addr)).json()
		except Exception as e:
			print(e)
			print_exc(file=open("log.txt", "a"))
		if obj is None:
			print("Address Does Not Exist")
			return "Error Getting {}".format(addr)
		addrObj = {'name': name, 'type': 'BTC', 'addr': obj['address'], 'n_txs': obj['n_tx'], 'minTx': minTx, 'maxTime': maxTime, 'txs': []}
		self.addrObj = addrObj
		with self.driver.session() as session:
			session.run("MERGE (a:BTC {addr:$addr}) "
						"ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.maxTime = {maxTime} "
						"ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.maxTime = {maxTime}", name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], maxTime = maxTime)
		if maxTime < 0 or maxTime is None: 
			return addrObj
		else:
			return self.threadsBTC(addrObj, )

	def threadsBTC(self, addrObj):
		self.done = False
		self.page = 0
		threads = []
		with self.driver.session() as session:
			lastTxid = session.run("Match (a:BTC)-[r]->(b:BTC) WHERE (a.addr = {addr} OR b.addr = {addr}) AND NOT r.isTotal "
										"RETURN r.txid ORDER BY r.epoch DESC LIMIT 1", addr = addrObj['addr'])
			lastTxid = lastTxid.single()
		if lastTxid is not None:
			lastTxid = lastTxid[0]
		else:
			lastTxid = ''
		dataThread = Thread(target=self.databaseThread, args=(addrObj, ))
		dataThread.start()
		for x in range(0, len(proxies)):
			threads.append(Thread(target=self.getTxs, args = (x, addrObj, lastTxid)))
			threads[x].start()
		for x in range(0, len(proxies)):
			threads[x].join()
		self.queue.put(None)
		dataThread.join()
		print("Done with all Threads")
		return str(self.addrObj)

	def refresh(self):
		#set lastTxId
		with self.driver.session() as session:
			nodes = session.run("MATCH (n:BTC) RETURN n")
			if nodes is not None:
				for node in nodes:
					node = node.get(node.keys()[0])
					obj = (requests.get(self.btcUrl + node['addr'])).json()
					addrObj = { 'addr': obj['address'], 'balance': float(obj['final_balance']/satoshi)}
					session.run("MATCH (a:BTC) WHERE a.addr = {addr} "
								"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch}", addr = addrObj['addr'], balance = addrObj['balance'], 
								lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
					if "minTx" in node and "maxTime" in node:
						self.done = False
						self.page = 0
						addrObj = { 'addr': obj['address'], 'type': 'BTC', 'n_txs': obj['n_tx'], 'minTx': node['minTx'], 'maxTime': node['maxTime'], 'txs': []}
						self.addrObj = addrObj
						self.threadsBTC(addrObj, )
			nodes = session.run("MATCH (n:USDT) RETURN n")
			if nodes is not None:
				for node in nodes:
					node = node.get(node.keys()[0])
					obj = self.usdtRequest(node['addr'], 1, 0)
					if 'error' in obj and obj['error']:
						return
					for coin in obj['balance']:
						if int(coin['id']) == 31:
							addrObj = { 'addr': obj['address'], 'balance': float(coin['value'])/satoshi}
							session.run("MATCH (a:USDT) WHERE a.addr = {addr} "
										"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch}", 
										addr = addrObj['addr'], balance = addrObj['balance'], lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
							break
					if "minTx" in node and "maxTime" in node:
						self.done = False
						self.page = 1
						addrObj = { 'addr': obj['address'], 'type': 'USDT', 'minTx': node['minTx'], 'maxTime': node['maxTime'], 'txs': []}
						self.addrObj = addrObj
						self.threadsUSDT(addrObj, )
			print("Addresses Updated")

	def collapse(self):
		with self.driver.session() as session:
			nodes = session.run("MATCH (a)-[r]->(b) WITH a, b, count(r) as rCount, SUM(toInt(r.amount)) as total " 
								"WHERE rCount > 1 RETURN a.addr, b.addr, total, labels(a)[0], labels(b)[0]")
			session.run("Match ()-[r {isTotal:True}]->() detach delete r")
			if nodes is not None:
				for node in nodes:
					aAddr = node.get(node.keys()[0])
					bAddr = node.get(node.keys()[1])
					total = node.get(node.keys()[2]) 
					aType = node.get(node.keys()[3]) 
					bType = node.get(node.keys()[4]) 
					session.run("MATCH (a:"+ aType + " {addr:$aAddr}), (b:" + bType + " {addr:$bAddr}) "
								"CREATE (a)-[r:`" + numWithCommas(total) + "` {isTotal:$isTotal, amount:$amount, lastUpdate:$lastUpdate, epoch:$epoch}]->(b) ",
								aAddr = aAddr, bAddr = bAddr, isTotal = True, amount = total, 
								lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
		print("Total Transactions Updated")

	def close(self):
		self.driver.close()