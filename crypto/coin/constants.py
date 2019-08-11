import sys
import requests
import json
import time
#import ctypes
from threading import Thread, Lock
from lxml import html
from random import randint
from traceback import print_exc

#kernel32 = ctypes.windll.kernel32
#kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
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
		'http':'http://lum-customer-hl_9579c5ab-zone-widow16-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow17-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow18-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow19-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow20-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow001-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow002-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow003-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow004-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow005-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow006-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow007-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow008-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow009-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow010-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow011-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow012-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow013-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow014-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow015-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow016-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow017-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow018-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow019-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow020-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow021-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow022-country-us:widow123@zproxy.lum-superproxy.io:22225'
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
			proxy = None if num < 0 else proxies[num]
			proxyStr = 'None' if proxy is None else proxy['http']
			print('Checking USDT ' + addr + ' Page: ' + str(page), "Proxy: " + proxyStr)
			obj = requests.post(self.usdtUrl, data = {'addr': addr, 'page': page}, proxies = proxy)
			print(obj)
			if obj is None or obj.status_code != 200:
				return None
			else: 
				obj = obj.json()
				return obj
		except Exception as e:
			print("{} {} {}".format(bcolors.FAIL, e, bcolors.ENDC))
			print_exc(file=open("log.txt", "a"))
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
		for x in range(0, len(proxies)):
			threads[x].join()
		print("Done with all Threads")
		print("{} Added {} Transactions to {} {}".format(bcolors.OKGREEN, len(self.addrObj['txs']), self.addrObj['addr'], bcolors.ENDC))
		return str(self.addrObj)