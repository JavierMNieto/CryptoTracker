from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404, render
from neo4j.v1 import GraphDatabase
import pprint
import json
import math
from pyvis.network import Network
from . import constants

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(
    constants.neo4j['user'], constants.neo4j['pass']))

# Create your views here.

def numWithCommas(num):
	return ("{:,}".format(num))

def search(request, id):
	#net = Network()
	with driver.session() as session:
		if id == '0':
			txs = session.run("MATCH (a:USDT)-[r:USDTTX]->(b:USDT) WHERE NOT r.isTotal "
							"RETURN a,b,r ORDER BY r.epoch DESC")
			addrs = session.run("MATCH (a:USDT)-[r]->(b:USDT) "
								"WITH DISTINCT a,b, count(r) AS sstcount "
								"MATCH p=(a)-[r]->(b) "
								"WHERE sstcount = 1 OR r.isTotal = True "
								"RETURN a, b, r")
			id = 'All'
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
			"color": "green",
			"label": aNode['name'],
			"value": 10.0 + float(aNode['balance'] or "0")/100000000,
			"title": ("Address: {}<br> "
						"Balance: {}<br> "
						"Last Updated: {}").format(aNode['addr'], numWithCommas(float(aNode['balance'] or "0")), aNode['lastUpdate'])
		}
		bNode = nodes.get('b')
		bNode = {
			"id": bNode.id,
			"color": "green",
			"label": bNode['name'],
			"value": 10.0 + float(bNode['balance'] or "0")/100000000,
			"title": ("Address: {}<br> "
						"Balance: {}<br> "
						"Last Updated: {}").format(bNode['addr'], numWithCommas(float(bNode['balance'] or "0") ), bNode['lastUpdate'])
		}
		rel   = nodes.get('r')
		rel2  = rel
		rel   = {
			"from": aNode['id'],
			"to": bNode['id'],
			"value": float(rel['amount']),
			"source": aNode['label'],
			"target": bNode['label'],
			"amount": numWithCommas(float(rel['amount'] or "0"))
			#"title": ("Collapsed: True<br> "
			#			"# of Txs: {}<br> "
			#			"Total: {}<br> "
			#			"Average Tx Amount: {}<br> "
			#			"Last Updated: {}").format(numWithCommas(rel2['TxsNum']), numWithCommas(rel2['amount']), 
			#								numWithCommas(rel2['avgTxAmt']), rel2['lastUpdate'])
		}
		if rel2['isTotal']:
			rel['title'] = ("Collapsed: True<br> "
							"# of Txs: {}<br> "
							"Total: {}<br> "
							"Average Tx Amount: {}<br> "
							"Last Updated: {}").format(numWithCommas(rel2['TxsNum']), numWithCommas(rel2['amount']), 
											numWithCommas(rel2['avgTxAmt']), rel2['lastUpdate'])
		else:
			rel['title'] = ("Collapsed: True<br> "
							"Txid: {}<br> "
							"Total: {}<br> "
							"Time: {}").format(rel2['txid'], numWithCommas(float(rel2['amount'])), rel2['time'])
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
			#net.add_node(aNode['id'], size = aNode['value'], title = aNode['title'], label = aNode['label'], color = aNode['color'])
			data['nodes'].append(aNode)
		if not bExists:
			#net.add_node(bNode['id'], size = bNode['value'], title = bNode['title'], label = bNode['label'], color = bNode['color'])
			data['nodes'].append(bNode)
		#net.add_edge(rel['from'], rel['to'], title = rel['title'], arrowStrikeThrough = rel['arrowStrikeThrough'], 
					#physics = rel['physics'], value = rel['value'])
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
			"value": float(rel['amount']),
			"source": aNode['label'],
			"target": bNode['label'],
			"amount": numWithCommas(float(rel['amount'] or "0")),
			"time": rel['time'],
			"txid": rel['txid'],
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
	#net.show_buttons(filter_=['nodes', 'edges', 'physics'])
	#net.save_graph('graph.html')
	#net.add_nodes(nodes['ids'], value = nodes['values'], title = nodes['titles'], label = nodes['labels'], color = nodes['colors'])
	return render(request, 'usdt/test.html', {'search': id, 'nodes': data['nodes'], 'edges': data['edges']})

def home(request):
	x = []
	#print('here')
	with driver.session() as session:
		results = session.run("MATCH (a:USDT) WHERE a.minTx IS NOT NULL RETURN a.name")
		for record in results:
			x.append(record['a.name'])
		#print(x)
	search = {'search': x}
	return render(request, 'usdt/index.html', search)

def nav(request):
    return render(request, 'usdt/navbar.html')