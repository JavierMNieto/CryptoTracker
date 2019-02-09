from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404, render
from neo4j.v1 import GraphDatabase
import pprint
import json
import math
import time
from urllib.parse import unquote
from pyvis.network import Network
from . import constants

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))
img = "data:image/png;base64,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"
# Create your views here.

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def search(request, id):
	mainAddr = None
	id = unquote(id)
	
	with driver.session() as session:
		if id == '0':
			txs = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE NOT r.isTotal "
							"RETURN a,b,r ORDER BY r.epoch DESC")
			addrs = session.run("MATCH (a:BTC)-[r]->(b:BTC) "
								"WITH DISTINCT a,b, count(r) AS sstcount "
								"MATCH p=(a)-[r]->(b) "
								"WHERE sstcount = 1 OR r.isTotal = True "
								"RETURN a, b, r")
			mainAddr = {
				"label": "All Addresses",
				"balance": 0
			}
		elif '[' in id:
			id = json.loads(id)
			addrsText = "-"
			label = "-"
			for addr in id:
				addrsText += " OR (a.name = '{}' OR  b.name = '{}')".format(addr, addr)
				label += ", {}".format(addr)
			addrsText = addrsText.split('- OR', 1)[1]
			label = label.split('-, ', 1)[1]
			print(addrsText)
			txs = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE(" + addrsText + ") AND NOT r.isTotal "
								"RETURN a,b,r ORDER BY r.epoch DESC")
			addrs = session.run("MATCH (a:BTC)-[r]->(b:BTC) "
								"WHERE(" + addrsText + ") "
								"WITH DISTINCT a,b, count(r) AS sstcount "
								"MATCH p=(a)-[r]->(b) "
								"WHERE sstcount = 1 OR r.isTotal = True "
								"RETURN a, b, r")
			mainAddr = {
				"label": label,
				"balance": 0
			}
		else:
			txs = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE (a.name = {name} OR b.name = {name}) AND NOT r.isTotal "
								"RETURN a,b,r ORDER BY r.epoch DESC", name = id)
			addrs = session.run("MATCH (a:BTC)-[r]->(b:BTC) "
								"WHERE (a.name = {name} OR b.name = {name}) "
								"WITH DISTINCT a,b, count(r) AS sstcount "
								"MATCH p=(a)-[r]->(b) "
								"WHERE sstcount = 1 OR r.isTotal = True "
								"RETURN a, b, r", name = id)
	data = {
		'nodes': [],
		'edges': {
			'collapsed': [],
			'all': []
		}
	}

	for nodes in addrs:
		aNode = nodes.get('a')
		aNode = {
			"id": aNode.id,
			"label": aNode['name'],
			"address": aNode['addr'],
			"balance": float(aNode['balance'] or 0),
			"group": aNode['wallet'] or "",
			"lastUpdate": aNode['epoch'] or time.time(),
			"url": "/btc/search/{}".format(aNode['name']) if aNode['minTx'] is not None else "https://blockexplorer.com/address/{}".format(aNode['addr']),
			"walletName": aNode['walletName'] or "",
			"value": 10.0 + float(aNode['balance'] or 0)/100000000,
			"img": img,
			"title": ("Address: {}<br> "
						"Balance: {}<br> "
						"Wallet: {}<br> "
						"Last Updated: {}").format(aNode['addr'], numWithCommas(float(aNode['balance'] or "0")), 
													"None" if aNode['walletName'] is None or aNode['walletName'] == '' else aNode['walletName'], aNode['lastUpdate'])
		}
		bNode = nodes.get('b')
		bNode = {
			"id": bNode.id,
			"label": bNode['name'],
			"address": bNode['addr'],
			"balance": float(bNode['balance'] or 0),
			"group": bNode['wallet'] or "",
			"lastUpdate": bNode['epoch'] or time.time(),
			"url": "/btc/search/{}".format(bNode['name']) if bNode['minTx'] is not None else "https://blockexplorer.com/address/{}".format(bNode['addr']),
			"walletName": bNode['walletName'] or "",
			"value": 10.0 + float(bNode['balance'] or 0)/100000000,
			"img": img,
			"title": ("Address: {}<br> "
						"Balance: {}<br> "
						"Wallet: {}<br> "
						"Last Updated: {} ").format(bNode['addr'], numWithCommas(float(bNode['balance'] or "0") ), 
													"None" if bNode['walletName'] is None or bNode['walletName'] == '' else bNode['walletName'], bNode['lastUpdate'])
		}
		rel   = nodes.get('r')
		rel   = {
			"from": aNode['id'],
			"to": bNode['id'],
			"id": rel.id,
			"value": float(rel['amount'] or 0),
			"source": aNode['label'],
			"target": bNode['label'],
			"amount": float(rel['amount'] or 0),
			"txsNum": int(rel['txsNum'] or 1.0),
			"lastUpdate": rel['epoch'] or rel['time'] or time.time(),
			"avgTx": float(rel['avgTxAmt'] or rel['amount'] or 0),
			"img": img,
			"color": {
				"color": "#F9A540"
			},
			"sourceUrl": "/btc/search/{}".format(aNode['label']) if aNode['url'] != ''
						else "https://blockexplorer.com/address/{}".format(aNode['label']),
			"targetUrl": "/btc/search/{}".format(bNode['label']) if aNode['url'] != ''
						else "https://blockexplorer.com/address/{}".format(bNode['label']),
			"title": ("Collapsed: True<br> "
						"# of Txs: {}<br> "
						"Total: {}<br> "
						"Average Tx Amount: {}<br> "
						"Last Updated: {}").format(numWithCommas(rel['txsNum'] or 1.0), numWithCommas(rel['amount']), 
										numWithCommas(rel['avgTxAmt'] or rel['amount']), rel['lastUpdate'] or rel['time'])
		}

		aExists = False
		bExists = False
		for node in data['nodes']:
			if node['id'] == aNode['id']:
				aExists = True
			if node['id'] == bNode['id']:
				bExists = True
			if aExists and bExists:
				break
		if not aExists:
			if mainAddr == None and aNode['label'] == id:
				mainAddr = aNode
				mainAddr['minTx'] = nodes.get('a')['minTx']
				mainAddr['tx_since'] = nodes.get('a')['tx_since']
				mainAddr['url'] = "https://blockexplorer.com/address/{}".format(mainAddr['address'])
			data['nodes'].append(aNode)
		if not bExists:
			if mainAddr == None and bNode['label'] == id:
				mainAddr = bNode
				mainAddr['minTx'] = nodes.get('b')['minTx']
				mainAddr['tx_since'] = nodes.get('b')['tx_since']
				mainAddr['url'] = "https://blockexplorer.com/address/{}".format(mainAddr['address'])
			data['nodes'].append(bNode)
		data['edges']['collapsed'].append(rel)
	for nodes in txs:
		aNode = nodes.get('a')
		aNode = {
			"id": aNode.id,
			"label": aNode['name'],
			"isKnown": True if aNode['minTx'] is not None else False
		}
		bNode = nodes.get('b')
		bNode = {
			"id": bNode.id,
			"label": bNode['name'],
			"isKnown": True if bNode['minTx'] is not None else False
		}
		rel   = nodes.get('r')
		rel   = {
			"from": aNode['id'],
			"to": bNode['id'],
			"id": rel.id,
			"value": float(rel['amount']),
			"source": aNode['label'],
			"target": bNode['label'],
			"amount": float(rel['amount'] or "0"),
			"time": rel['epoch'],
			"txid": rel['txid'],
			"img": img,
			"color": {
				"color": "#F9A540"
			},
			"txidUrl": "https://blockexplorer.com/tx/{}".format(rel['txid']),
			"sourceUrl": "/btc/search/{}".format(aNode['label']) if aNode['isKnown'] 
						else "https://blockexplorer.com/address/{}".format(aNode['label']),
			"targetUrl": "/btc/search/{}".format(bNode['label']) if bNode['isKnown'] 
						else "https://blockexplorer.com/address/{}".format(bNode['label']),
			"title": ("Collapsed: False<br> "
						"Txid: {}<br> "
						"Total: {}<br> "
						"Time: {}").format(rel['txid'], numWithCommas(float(rel['amount'])), rel['time'])
		}
		data['edges']['all'].append(rel)
	if len(data['edges']['collapsed']) < 1:
		mainAddr = None
	return render(request, 'coin/coin.html', {'search': mainAddr, 'nodes': data['nodes'], 'edges': data['edges']})