import sys
import requests
import json
import time
import pprint
import ctypes
from threading import Thread, Lock
from lxml import html

satoshi = 100000000.0
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

neo4j   = {
	'user': 'neo4j',
	'pass': '2282002',
	'url': 'bolt://localhost:7687'
}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def logPrint(*args, **kwargs):
    print(*args, file=open("log.txt", "a"), **kwargs)

proxies = [
	{
		'http':'socks5://x3234593:ZpSMx9ktPg@proxy-nl.privateinternetaccess.com:1080',
		'https':'socks5://x3234593:ZpSMx9ktPg@proxy-nl.privateinternetaccess.com:1080'
	},
	{

		'http':'http://lum-customer-hl_4856a1e8-zone-static-country-us:uc9xcu9fcfpi@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-static-country-us:uc9xcu9fcfpi@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone1-country-us:l2b77dfwx1jz@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone1-country-us:l2b77dfwx1jz@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone2-country-us:1zbuhqzyenlo@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone2-country-us:1zbuhqzyenlo@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone3-country-us:ubzmd1szj4i4@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone3-country-us:ubzmd1szj4i4@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone4-country-us:phcbsz4yzew0@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone4-country-us:phcbsz4yzew0@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone5-country-us:75m0632dewt7@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone5-country-us:75m0632dewt7@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone6-country-us:vdy91ua9vjd3@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone6-country-us:vdy91ua9vjd3@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone7-country-us:ymbfcmpyg5pl@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone7-country-us:ymbfcmpyg5pl@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone8-country-us:fe7wys4boaqp@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone8-country-us:fe7wys4boaqp@zproxy.lum-superproxy.io:22225'
	}
]

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
	def __init__(self, btcUrl, driver):
		self.btcUrl = btcUrl
		self.driver = driver
		self.mutex = Lock()
		self.done = False
		self.page = 0
		self.addrObj = {}

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
					print("No More Transactions Left")
				else:
					print("Offset Exceeded 7500, moving on...")
				self.mutex.acquire()
				self.done = True
				self.mutex.release()
				return 0
			i = 0
			for tx in obj['txs']:
				if addrObj['lastTxTime'] > tx['time'] or addrObj['tx_since'] > tx['time']:
					if addrObj['lastTxTime'] > tx['time']:
						print("No New Transactions") 
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
					self.upTx(sortedTx, )
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

	def threadsBTC(self, addrObj):
		self.done = False
		self.page = 0
		self.addrObj = addrObj
		threads = []
		for x in range(0, len(proxies)):
			threads.append(Thread(target=self.getTxs, args = (x, addrObj)))
			threads[x].start()
		for x in range(0, len(proxies)):
			threads[x].join()
		print("Done with all Threads")
		print("{} Added {} Transactions to {} {}".format(bcolors.OKGREEN, len(self.addrObj['txs']), self.addrObj['addr'], bcolors.ENDC))
		self.collapse()
		return str(self.addrObj)
	
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