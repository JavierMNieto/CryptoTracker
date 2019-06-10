import requests
import json
import time
import pprint
from urllib.parse import parse_qs as pq
from neo4j.v1 import GraphDatabase
from constants import *
from lxml import html
from random import randint
from traceback import print_exc
from threading import Thread, Lock
import queue
#import ctypes

#kernel32 = ctypes.windll.kernel32
#kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def numWithCommas(num):
	return ("{:,}".format(num))

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Search: 
	def __init__(self, btcUrl, usdtUrl, neo4j):
		self.btcUrl = btcUrl
		self.usdtUrl = usdtUrl
		self.driver = GraphDatabase.driver(neo4j['url'], auth=(neo4j['user'], neo4j['pass']))
		self.mutex = Lock()
		self.done = False
		self.page = 0
		self.addrObj = {}
		self.sAddrsQ = queue.Queue()

	def checkParams(self, environ):
		params = pq(environ['QUERY_STRING'])
		return 'addr' in params

	def usdtRequest(self, addr, page, num):
		try: 
			proxy = None if num < 0 else proxies[num]
			proxyStr = 'None' if proxy is None else proxy['http']
			print('Checking USDT ' + addr + ' Page: ' + str(page), "Proxy: " + proxyStr)
			obj = requests.post(self.usdtUrl, data = {'addr': addr, 'page': page}, proxies = proxy)
			if obj is None or obj.status_code != 200:
				return None
			else: 
				obj = obj.json()
				return obj
		except Exception as e:
			print("{} {} {}".format(bcolors.FAIL, e, bcolors.ENDC))
			print_exc(file=open("log.txt", "a"))
			return self.usdtRequest(addr, page, randint(-1, len(proxies)-1))

	def getTxs(self, threadNum, addrObj):
		while not self.done:
			offset = 0
			self.mutex.acquire()
			offset = self.page
			self.page += 50
			self.mutex.release()
			print('Checking BTC {} at Offset {} with Thread {}'.format(addrObj['addr'], offset, threadNum))
			url = self.btcUrl + addrObj['addr'] + '?&offset=' + str(offset)
			try:
				obj = requests.get(url).json()
			except:
				continue
			if len(obj['txs']) == 0 or offset > 7500:
				if len(obj['txs']) == 0:
					print("No More Transactions Left for Thread " + str(threadNum))
				else:
					print("Offset Exceeded 7500 at Thread {}, moving on...".format(str(threadNum)))
				self.mutex.acquire()
				self.done = True
				self.mutex.release()
				return 0
			i = 0
			for tx in obj['txs']:
				if addrObj['lastTxTime'] > tx['time'] or addrObj['tx_since'] > tx['time']:
					if addrObj['lastTxTime'] > tx['time']:
						print("No New Transactions for Thread " + str(threadNum)) 
					self.mutex.acquire()
					self.done = True
					self.mutex.release()
					break
				i += 1	
				exist = self.driver.session().run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE r.txid = {txid} RETURN r.txid LIMIT 1", txid = tx['hash'])
				exist = exist.single()
				if exist is not None:
					continue
				for inTx in tx['inputs']:
					if len(inTx['prev_out']['addr']) > 34:
						continue
				for outTx in tx['out']:
					if len(outTx['addr']) > 34:
						continue
				inputs  = {}
				outputs = {}
				amount  = None
				for inTx in tx['inputs']:
					if inTx['prev_out']['addr'] != addrObj['addr']:
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
				if amount is not None and float(amount) > float(addrObj['minTx']):
					sortedTx = {'addr': addrObj['addr'], 'txid': tx['hash'], 'time': tx['time'], 'inputs': inputs, 'outputs': outputs, 'amount': amount}
					#pprint.pprint(sortedTx)
					self.upTx(sortedTx, )
			if self.done:
				print("{} All Transactions Collected for Thread {} {}".format(bcolors.OKBLUE, threadNum, bcolors.ENDC))
				return 0
		return 0

	def getUTxs(self, threadNum, addrObj):
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
				print("Max Transactions Requested From OmniExplorer for Thread " + str(threadNum))
				#wait
				starttime = time.time()
				wait = True
				while wait:
					print("Waiting on Thread {}".format(threadNum))
					time.sleep(60.0 - ((time.time() - starttime) % 60.0))
					wait = False
					obj = self.usdtRequest(addrObj['addr'], currPage, threadNum)
					if obj is None or ('error' in obj and obj['error']):
						wait = True
			for tx in obj['transactions']:
				if addrObj['lastTxTime'] > tx['blocktime'] or addrObj['tx_since'] > tx['blocktime']:
					if addrObj['lastTxTime'] > tx['blocktime']:
						print("No New Transactions for Thread " + str(threadNum))
					self.mutex.acquire()
					self.done = True
					self.mutex.release()
					break
				exist = self.driver.session().run("MATCH (a:USDT)-[r:USDTTX]->(b:USDT) WHERE r.txid = {txid} RETURN r.txid LIMIT 1", txid = tx['txid'])
				exist = exist.single()
				isNotValid = 'valid' not in tx or not tx['valid'] or int(tx['propertyid']) != 31 or (int(tx['type_int']) != 0 and int(tx['type_int']) != 55) or float(tx['amount']) < addrObj['minTx'] or exist is not None 
				if isNotValid:
					continue
				inName = tx['sendingaddress']
				outName = tx['referenceaddress']
				sortedTx = {'addr': addrObj['addr'], 'txid': tx['txid'], 'time': tx['blocktime'], 'inputs': {inName: float(tx['amount'])}, 'outputs': {outName: (float(tx['amount']) - float(tx['fee']))}, 'amount': tx['amount']}
				self.upTx(sortedTx, )
			if self.page >= obj['pages'] or self.page > 1500:
				if self.page > 1500:
					print("Transactions Checked Exceeded 1500 Pages on Thread {}, Moving On...".format(str(threadNum)))
				else:
					print("No More Transactions Left for Thread " + str(threadNum))
				self.mutex.acquire()
				self.done = True
				self.mutex.release()
			if self.done:
				print("{} All Transactions Collected for Thread {} {}".format(bcolors.OKBLUE, threadNum, bcolors.ENDC))
				return 0
		return 0

	def upTx(self, tx):
		addrObj = self.addrObj
		for inName, inValue in tx['inputs'].items():
			for outName, outValue in tx['outputs'].items():
				if inName == outName:
					continue
				val = 0
				if inName == tx['addr'] and len(tx['inputs']) == 1:
					val = outValue
				else:
					val = inValue
				if float(val) < addrObj['minTx']:
					continue
				newAddr = inName if outName == tx['addr'] else outName
				with self.driver.session() as session:
					wallet = session.run("MERGE (a:" + addrObj['type'] + " {addr:$addr}) "
								"ON CREATE SET a.name = {addr}, a.wallet = '' "
								"RETURN a.wallet", addr = newAddr)
					wallet = wallet.single()
					session.run("MATCH (a:" + addrObj['type'] + "), (b:" + addrObj['type'] + ") WHERE a.addr = {aAddr} AND b.addr = {bAddr} "
								"CREATE (a)-[:" + addrObj['type'] + "TX {txid:$txid, time:$time, amount:$amount, epoch:$epoch, isTotal:$isTotal}]->(b)",
								aAddr = inName, bAddr = outName, txid = tx['txid'], time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['time'])), 
								amount = tx['amount'], epoch = tx['time'], isTotal = False)
					if wallet is None or wallet.value() == '':
						if addrObj['type'] == 'USDT':
							session.run("MATCH (a:USDT {addr:$addr}) "
										"SET a.wallet = 'usdt'", addr = newAddr)
						elif addrObj['type'] == 'BTC':
							try:
								wallet = (requests.get("https://www.walletexplorer.com/address/" + newAddr)) # get page
								wallet = html.fromstring(wallet.content) # get html
								wallet = wallet.xpath('//div[@class="walletnote"]//a')
							except:
								wallet = None

							if wallet is None or len(wallet) < 1:
								wallet = ''
							else: 
								wallet = wallet[0].get('href') # get wallet text
								wallet = wallet.replace('/wallet/', '')
							
							try:
								walletName = (requests.get("https://bitinfocharts.com/bitcoin/address/" + newAddr)) # get page
								walletName = html.fromstring(walletName.content) # get html
								walletName = walletName.xpath('//table[@class="table table-striped table-condensed"]//a')
							except:
								walletName = None

							if walletName is None or len(walletName) < 1:
								walletName = wallet
							else:
								walletName = walletName[0].get('href') # get wallet text
								walletName = walletName.replace('../wallet/', '')

							session.run("MATCH (a:BTC {addr:$addr}) "
										"SET a.wallet = {wallet}, a.walletName = {walletName}", addr = newAddr, wallet = wallet, walletName = walletName)
							self.addrObj['txs'].append(tx)
		#print("Added {} Transactions to {}".format(len(self.addrObj['txs']), self.addrObj['name']))

	def threadsUSDT(self, addrObj):
		self.done = False
		self.page = 1
		self.addrObj = addrObj
		threads = []
		for x in range(0, len(proxies)):
			threads.append(Thread(target=self.getUTxs, args = (x, addrObj)))
			threads[x].start()
		for x in threads:
			x.join(600)
		print("Done with all Threads")
		print("{} Added {} Transactions to {} {}".format(bcolors.OKGREEN, len(self.addrObj['txs']), self.addrObj['addr'], bcolors.ENDC))
		return str(self.addrObj)

	def threadsBTC(self, addrObj):
		self.done = False
		self.page = 0
		self.addrObj = addrObj
		threads = []
		for x in range(0, len(proxies)):
			threads.append(Thread(target=self.getTxs, args = (x, addrObj)))
			threads[x].start()
		for x in threads:
			x.join(600)
		print("Done with all Threads")
		print("{} Added {} Transactions to {} {}".format(bcolors.OKGREEN, len(self.addrObj['txs']), self.addrObj['addr'], bcolors.ENDC))
		return str(self.addrObj)

	def refresh(self):
		#set lastTxId
		print("Refreshing Addresses")
		with self.driver.session() as session:
			nodes = session.run("MATCH (n:BTC) WHERE n.minTx IS NOT NULL RETURN n")
			if nodes is not None:
				for node in nodes:
					node = node.get(node.keys()[0])
					try:
						obj = requests.get(self.btcUrl + node['addr'])
						if not obj.status_code:
								print("{} Waiting {} Seconds {}".format(bcolors.BOLD, 10, bcolors.ENDC))
								time.sleep(10)
								obj = requests.get(self.btcUrl + addrObj['addr'])
						if obj.status_code:
							obj = obj.json()
						else:
							continue
					except Exception as e:
						print("{} {} {}".format(bcolors.FAIL, e, bcolors.ENDC))
						print_exc(file=open("log.txt", "a"))
						continue
					addrObj = { 'addr': obj['address'], 'balance': float(obj['final_balance']/satoshi)}
					lastTime = session.run("MATCH (a:BTC) WHERE a.addr = {addr} "
											"WITH a, a.epoch as lastTime "
											"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch} "
											"RETURN CASE lastTime WHEN NULL THEN 0 ELSE lastTime END", 
											addr = addrObj['addr'], balance = addrObj['balance'], 
											lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), 
											epoch = time.time())
					lastTime = lastTime.single()
					if lastTime is None:
						lastTime = 0
					else:
						lastTime = lastTime[0]
					self.done = False
					self.page = 0
					addrObj = { 'addr': obj['address'], 'type': 'BTC', 'n_txs': obj['n_tx'], 
								'minTx': node['minTx'], 'tx_since': node['tx_since'], 'lastTxTime': lastTime, 'txs': []}
					self.threadsBTC(addrObj, )
			print(bcolors.OKBLUE + "Done With Main BTC Addresses" + bcolors.ENDC)
			nodes = session.run("MATCH (n:USDT) WHERE n.minTx IS NOT NULL RETURN n")
			if nodes is not None:
				for node in nodes:
					node = node.get(node.keys()[0])
					obj = self.usdtRequest(node['addr'], 1, randint(-1, len(proxies)-1))
					if obj is None or 'error' in obj and obj['error']:
						continue
					for coin in obj['balance']:
						if int(coin['id']) == 31:
							addrObj = { 'addr': obj['address'], 'balance': float(coin['value'])/satoshi}
							lastTime = session.run("MATCH (a:USDT) WHERE a.addr = {addr} "
													"WITH a, a.epoch as lastTime "
													"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch} "
													"RETURN CASE lastTime WHEN NULL THEN 0 ELSE lastTime END", 
													addr = addrObj['addr'], balance = addrObj['balance'], 
													lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
							lastTime = lastTime.single()
							if lastTime is None:
								lastTime = 0
							else:
								lastTime = lastTime[0]
							break
					self.done = False
					self.page = 1
					addrObj = { 'addr': obj['address'], 'type': 'USDT', 'minTx': node['minTx'],
								'tx_since': node['tx_since'], 'lastTxTime': lastTime, 'txs': []}
					self.addrObj = addrObj
					self.threadsUSDT(addrObj, )
			print(bcolors.OKBLUE + "Done With Main USDT Addresses" + bcolors.ENDC)
			nodes = session.run("MATCH (n) WHERE n.minTx IS NULL RETURN n")
			self.sAddrsQ = queue.Queue()
			threads = []
			for node in nodes:
				node  = node.get('n')
				self.sAddrsQ.put({
					'addr': node['addr'],
					'type': next(iter(node.labels))
				})
			for x in range(0, len(proxies)):
				threads.append(Thread(target=self.smallRefresh, args = (x,)))
				threads[x].start()
			for thread in threads:
				thread.join()
			self.sAddrsQ.join()
			print("{} Addresses Updated as of {} {}".format(bcolors.OKGREEN, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), bcolors.ENDC))

	def smallRefresh(self, threadNum):
		while not self.sAddrsQ.empty():
			addrObj = self.sAddrsQ.get()
			if addrObj is None:
				print('Thread {} is Done'.format(threadNum))
				print(self.sAddrsQ.qsize())
				break
			self.smallNodes(addrObj, threadNum)
			if self.sAddrsQ.unfinished_tasks % 100 == 0:
				print("{} {} Addresses Left {}".format(bcolors.HEADER, self.sAddrsQ.unfinished_tasks, bcolors.ENDC))
				#print(self.sAddrsQ.qsize())
			self.sAddrsQ.task_done()
		return 0

	def smallNodes(self, addrObj, threadNum):
		with self.driver.session() as session:
			try:
				if addrObj['type'] == 'BTC':
					if len(addrObj['addr']) > 35:
						return 0
					obj = requests.get(self.btcUrl + addrObj['addr'])
					if int(obj.status_code) != 200:
						print("{} Thread {} Waiting {} Seconds {}".format(bcolors.BOLD, threadNum, 10, bcolors.ENDC))
						time.sleep(10)
						obj = requests.get(self.btcUrl + addrObj['addr'])
					if obj.status_code:
						obj = obj.json()
					else:
						print("{} {} {}".format(bcolors.FAIL, "Error", bcolors.ENDC), "With {} {}".format(addrObj['type'], addrObj['addr']), "Thread {}".format(threadNum))
						return 0
					print('Checking BTC {} with Thread {}'.format(addrObj['addr'], threadNum))
					addrObj = { 'addr': obj['address'], 'balance': float(obj['final_balance']/satoshi)}
					session.run("MATCH (a:BTC) WHERE a.addr = {addr} "
								"WITH a, a.epoch as lastTime "
								"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch} ", 
								addr = addrObj['addr'], balance = addrObj['balance'], 
								lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), 
								epoch = time.time())
				elif addrObj['type'] == 'USDT':
					obj = self.usdtRequest(addrObj['addr'], 1, threadNum)
					if obj is None or 'error' in obj and obj['error']:
						return 0
					for coin in obj['balance']:
						if int(coin['id']) == 31:
							addrObj = { 'addr': obj['address'], 'balance': float(coin['value'])/satoshi}
							session.run("MATCH (a:USDT) WHERE a.addr = {addr} "
										"WITH a, a.epoch as lastTime "
										"SET a.balance = {balance}, a.lastUpdate = {lastUpdate}, a.epoch = {epoch} ", 
										addr = addrObj['addr'], balance = addrObj['balance'], 
										lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
							break
			except Exception as e:
				print("{} {} {}".format(bcolors.FAIL, e, bcolors.ENDC), "For {} {}".format(addrObj['type'], addrObj['addr']), "Thread {}".format(threadNum))
				print_exc(file=open("log.txt", "a"))

	def collapse(self):
		with self.driver.session() as session:
			nodes = session.run("MATCH (a)-[r]->(b) WITH a, b, count(r) as rCount, SUM(toInt(r.amount)) as total " 
								"WHERE rCount > 1 RETURN a.addr, b.addr, total, labels(a)[0], labels(b)[0], rCount")
			#session.run("Match ()-[r {isTotal:True}]->() detach delete r")
			if nodes is not None:
				for node in nodes:
					aAddr = node.get(node.keys()[0])
					bAddr = node.get(node.keys()[1])
					total = float(node.get(node.keys()[2])) 
					aType = node.get(node.keys()[3]) 
					bType = node.get(node.keys()[4])
					txsNum = float(node.get(node.keys()[5]))
					avgTotal = total/txsNum
					session.run("MATCH (a:"+ aType + " {addr:$aAddr}), (b:" + bType + " {addr:$bAddr}) "
								"MERGE (a)-[r:" + aType + "TX {isTotal:$isTotal}]->(b) "
								"ON CREATE SET r.amount = {amount}, r.lastUpdate = {lastUpdate}, r.epoch = {epoch}, r.avgTxAmt = {avgTxTotal}, r.txsNum = {txsNum} "
								"ON MATCH SET r.amount = {amount}, r.lastUpdate = {lastUpdate}, r.epoch = {epoch}, r.avgTxAmt = {avgTxTotal}, r.txsNum = {txsNum} ",
								aAddr = aAddr, bAddr = bAddr, isTotal = True, amount = total, avgTxTotal = avgTotal, txsNum = txsNum,
								lastUpdate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), epoch = time.time())
		print("Collapsed Transactions Updated as of {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))

	def close(self):
		self.driver.close()