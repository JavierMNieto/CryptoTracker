from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404, render
from neo4j.v1 import GraphDatabase
import pprint
from . import constants

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(
    constants.neo4j['user'], constants.neo4j['pass']))

# Create your views here.

def search(request, id):
	with driver.session() as session:
		txs = session.run("MATCH (a:USDT)-[r]->(b:USDT) WHERE (a.name = {name} OR b.name = {name}) AND NOT r.isTotal "
							"RETURN a,b,r ORDER BY r.epoch DESC", name = id)
		addrs = session.run("MATCH (a)-[r]-(b) "
				"WHERE (a.name = {name} OR b.addr = {name}) "
				"WITH DISTINCT a,b, count(r) AS sstcount "
				"MATCH p=(a)-[r]-(b) "
				"WHERE sstcount = 1 OR r.isTotal = True "
				"RETURN p")
	data = {
		'nodes': [],
		'edges': []		
	}
	for nodes in txs:
		aNode = nodes.get(nodes.keys()[0])
		bNode = nodes.get(nodes.keys()[1])
		rel   = nodes.get(nodes.keys()[2])
		tx = {'inAddr': aNode['addr'], 'outAddr': bNode['addr'], 'amount': rel['amount'], 'time': rel['time']}
		
	return render(request, 'usdt/test.html', {'search': id, 'data': tx})

def home(request):
	x = []
	print('here')
	with driver.session() as session:
		results = session.run("MATCH (a:USDT) WHERE a.minTx IS NOT NULL RETURN a.name")
		for record in results:
			x.append(record['a.name'])
		print(x)
	search = {'search': x}
	return render(request, 'usdt/index.html', search)

def nav(request):
    return render(request, 'usdt/navbar.html')
