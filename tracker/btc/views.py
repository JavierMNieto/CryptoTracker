from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404, render
from neo4j.v1 import GraphDatabase
from django.http import JsonResponse
from urllib.parse import unquote
from pyvis.network import Network
from . import constants
import pprint
import json
import math
import time
import ccxt

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))
img = "https://s2.coinmarketcap.com/static/img/coins/64x64/1.png"

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def getTxs(request):
	page = max(int(request.GET.get('page')) or 1, 1)
	name = request.GET.getlist('name[]') or None
	sort = request.GET.get('sort') or 'epoch'
	order = request.GET.get('order') or 'DESC'

	return JsonResponse(txData(page - 1, name=name, sort=sort, order=order), safe=False)

def txData(page, name=None, sort='epoch', order='DESC'):
	cmc = ccxt.coinmarketcap()
	btcPrice = float(cmc.fetch_ticker('BTC/USD')['last'])
	with driver.session() as session:
		if name:
			addrsText = '-'
			for addr in name:
				addrsText += " OR (a.name = '{}' OR  b.name = '{}')".format(addr, addr)
			addrsText = addrsText.split('- OR', 1)[1]
			data = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE(" + addrsText + ") AND NOT r.isTotal "
									"RETURN a,b,r ORDER BY r." + sort + " " + order + " SKIP {offSet} LIMIT 10", offSet = page*10)
		else:
			data = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE NOT r.isTotal "
								"RETURN a,b,r ORDER BY r." + sort + " " + order + " SKIP {offSet} LIMIT 10", offSet = page*10)
	edges = []
	for nodes in data:
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
			"value": float(rel['amount'] or 0)*btcPrice,
			"source": aNode['label'],
			"target": bNode['label'],
			"amount": float(rel['amount'] or 0),
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
		edges.append(rel)
	return edges

def search(request, id):
	if 'img' in str(id) and '{' in str(id):
		return render(request, 'coin/coin.html')
	mainAddr = None
	id = unquote(id)
	
	with driver.session() as session:
		if id == '0':
			txs = txData(0)
			totalTxs = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE NOT r.isTotal RETURN count(r) AS totalTxs").single().get('totalTxs')
			minTx	 = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE NOT r.isTotal RETURN r.amount ORDER BY r.amount ASC LIMIT 1").single().value()
			lastTx	 = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE NOT r.isTotal RETURN r.epoch ORDER BY r.epoch ASC LIMIT 1").single().value()
			mainAddr = {
				"label": "All Addresses",
				"name": None,
				"totalTxs": totalTxs,
				"minTx": minTx,
				"lastTx": lastTx,
				"balance": 0
			}
		elif '[' in id:
			id = json.loads(id)
			names = []
			txsText = '-'
			addrsText = '-'
			label = "-"
			isCategory = False
			for addr in id:
				if '.' in addr:
					label += ", {}".format(addr.split('.', 1)[1])
					isCategory = True
					continue
				names.append(addr)
				txsText += " OR (a.name = '{}' OR  b.name = '{}')".format(addr, addr)
				addrsText += " OR a.name = '{}'".format(addr)
				if not isCategory:
					label += ", {}".format(addr)
			txsText = txsText.split('- OR', 1)[1]
			addrsText = addrsText.split('- OR', 1)[1]
			label = label.split('-, ', 1)[1]
			txs = txData(0, name=names)
			totalTxs = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE(" + txsText + ") AND NOT r.isTotal RETURN count(r)").single().value()
			balance  = session.run("MATCH (a:BTC) WHERE(" + addrsText + ") RETURN SUM(a.balance)").single().value()
			minTx	 = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE(" + txsText + ") AND NOT r.isTotal RETURN r.amount ORDER BY r.amount ASC LIMIT 1").single().value()
			lastTx	 = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE(" + txsText + ") AND NOT r.isTotal RETURN r.epoch ORDER BY r.epoch ASC LIMIT 1").single().value()

			mainAddr = {
				"label": label,
				"name": names,
				"totalTxs": totalTxs,
				"minTx": minTx,
				"lastTx": lastTx,
				"balance": balance
			}
		else:
			totalTxs = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE (a.name = {name} OR b.name = {name}) AND NOT r.isTotal RETURN count(r)", name = id).single().value()
			minTx	 = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE (a.name = {name} OR b.name = {name}) AND NOT r.isTotal RETURN r.amount ORDER BY r.amount ASC LIMIT 1", name = id).single().value()
			lastTx	 = session.run("MATCH (a:BTC)-[r:BTCTX]->(b:BTC) WHERE (a.name = {name} OR b.name = {name}) AND NOT r.isTotal RETURN r.epoch ORDER BY r.epoch ASC LIMIT 1", name = id).single().value()

			addrInfo = session.run("MATCH (a:BTC) WHERE a.name = {name} RETURN a.balance as bal, a.addr as addr", name = id).single()
			addr = addrInfo.get('addr')
			bal  = addrInfo.get('bal')

			mainAddr = {
				"label": id,
				"name": [id],
				"address": addr,
				"totalTxs": totalTxs,
				"minTx": minTx,
				"lastTx": lastTx,
				"balance": bal
			}
			txs = txData(0, name=[id])
	return render(request, 'coin/coin.html', {'search': mainAddr, 'edges': txs})