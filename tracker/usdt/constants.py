import sys
import requests
import json
import time
import ctypes
from threading import Thread, Lock
from lxml import html
from random import randint
from traceback import print_exc

kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
satoshi = 100000000.0
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
	def __init__(self, usdtUrl, driver):
		self.usdtUrl = usdtUrl
		self.driver = driver
		self.mutex = Lock()
		self.done = False
		self.page = 0
		self.addrObj = {}

	def usdtRequest(self, addr, page, num):
		try: 
			proxy = 'None' if num < 0 or proxies[num] is None else str(proxies[num]['https'])
			print('Checking USDT ' + addr + ' Page: ' + str(page), "Proxy: " + proxy)
			obj = (requests.post(self.usdtUrl, data = {'addr': addr, 'page': page}, proxies = proxies[num])).json()
			if obj is None or ('error' in obj and obj['error']):
				return self.usdtRequest(addr, page, randint(-1, len(proxies)-1))
			else: 
				return obj
		except Exception as e:
			print("{} {} for {} {}".format(bcolors.FAIL, e, proxies[num], bcolors.ENDC))
			return self.usdtRequest(addr, page, randint(-1, len(proxies)-1))

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
				if addrObj['lastTxTime'] > tx['blocktime'] or addrObj['tx_since'] > tx['blocktime']:
					if addrObj['lastTxTime'] > tx['blocktime']:
						print("No New Transactions")
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
					print("Transactions Checked Exceeded 1500 Pages, Moving On...")
				else:
					print("No More Transactions Left")
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