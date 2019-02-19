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
img = "https://s2.coinmarketcap.com/static/img/coins/200x200/825.png"

# Create your views here.

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def search(request, id):
	mainAddr = None
	id = unquote(id)
	
	with driver.session() as session:
		if id == '0':
			txs = session.run("MATCH (a:USDT)-[r:USDTTX]->(b:USDT) WHERE NOT r.isTotal "
							"RETURN a,b,r ORDER BY r.epoch DESC")
			addrs = session.run("MATCH (a:USDT)-[r]->(b:USDT) "
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
			txs = session.run("MATCH (a:USDT)-[r:USDTTX]->(b:USDT) WHERE(" + addrsText + ") AND NOT r.isTotal "
								"RETURN a,b,r ORDER BY r.epoch DESC")
			addrs = session.run("MATCH (a:USDT)-[r]->(b:USDT) "
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
			txs = session.run("MATCH (a:USDT)-[r:USDTTX]->(b:USDT) WHERE (a.name = {name} OR b.name = {name}) AND NOT r.isTotal "
								"RETURN a,b,r ORDER BY r.epoch DESC", name = id)
			addrs = session.run("MATCH (a:USDT)-[r]->(b:USDT) "
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
			"group": aNode['wallet'] or 'usdt',
			"lastUpdate": aNode['epoch'] or time.time(),
			"url": "/usdt/search/{}".format(aNode['name']) if aNode['minTx'] is not None else "https://omniexplorer.info/address/{}".format(aNode['addr']),
			"webUrl": "https://omniexplorer.info/address/{}".format(aNode['addr']),
			"value": 25.0 + float(aNode['balance'] or 0)/100000000,
			"img": img,
			"title": ("Address: {}<br> "
						"Balance: {}<br> "
						"Last Updated: {}").format(aNode['addr'], numWithCommas(float(aNode['balance'] or "0")), aNode['lastUpdate'])
		}
		if aNode['label'] != aNode['address']:
			aNode['title'] = ("Name: {}<br> "
							"Address: {}<br> "
							"Balance: {}<br> "
							"Last Updated: {}").format(aNode['label'], aNode['address'], numWithCommas(aNode['balance']),
														time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime(aNode['lastUpdate'])))
		bNode = nodes.get('b')
		bNode = {
			"id": bNode.id,
			"label": bNode['name'],
			"address": bNode['addr'],
			"balance": float(bNode['balance'] or 0),
			"group": bNode['wallet'] or 'usdt',
			"lastUpdate": bNode['epoch'] or time.time(),
			"url": "/usdt/search/{}".format(bNode['name']) if bNode['minTx'] is not None else "https://omniexplorer.info/address/{}".format(bNode['addr']),
			"webUrl": "https://omniexplorer.info/address/{}".format(bNode['addr']),
			"value": 25.0 + float(bNode['balance'] or 0)/100000000,
			"img": img,
			"title": ("Address: {}<br> "
						"Balance: {}<br> "
						"Last Updated: {}").format(bNode['addr'], numWithCommas(float(bNode['balance'] or "0") ), bNode['lastUpdate'])
		}
		if bNode['label'] != bNode['address']:
			bNode['title'] = ("Name: {}<br> "
							"Address: {}<br> "
							"Balance: {}<br> "
							"Last Updated: {}").format(bNode['label'], bNode['address'], numWithCommas(bNode['balance']),
														time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime(bNode['lastUpdate'])))
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
				"color": "#26A17B"
			},
			"sourceUrl": "/usdt/search/{}".format(aNode['label']) if aNode['url'] != ''
						else "https://omniexplorer.info/address/{}".format(aNode['label']),
			"targetUrl": "/usdt/search/{}".format(bNode['label']) if aNode['url'] != ''
						else "https://omniexplorer.info/address/{}".format(bNode['label']),
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
				mainAddr['url'] = "https://omniexplorer.info/address/{}".format(mainAddr['address'])
			data['nodes'].append(aNode)
		if not bExists:
			if mainAddr == None and bNode['label'] == id:
				mainAddr = bNode
				mainAddr['minTx'] = nodes.get('b')['minTx']
				mainAddr['tx_since'] = nodes.get('b')['tx_since']
				mainAddr['url'] = "https://omniexplorer.info/address/{}".format(mainAddr['address'])
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
				"color": "#26A17B"
			},
			"txidUrl": "https://omniexplorer.info/tx/{}".format(rel['txid']),
			"sourceUrl": "/usdt/search/{}".format(aNode['label']) if aNode['isKnown'] 
						else "https://omniexplorer.info/address/{}".format(aNode['label']),
			"targetUrl": "/usdt/search/{}".format(bNode['label']) if bNode['isKnown'] 
						else "https://omniexplorer.info/address/{}".format(bNode['label']),
			"title": ("Collapsed: False<br> "
						"Txid: {}<br> "
						"Total: {}<br> "
						"Time: {}").format(rel['txid'], numWithCommas(float(rel['amount'])), rel['time'])
		}
		data['edges']['all'].append(rel)
	if len(data['edges']['collapsed']) < 1:
		data['edges'] = None
	return render(request, 'coin/coin.html', {'search': mainAddr, 'nodes': data['nodes'], 'edges': data['edges']})