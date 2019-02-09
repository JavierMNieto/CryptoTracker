from django.http import HttpResponse
from django.template import loader
from neo4j.v1 import GraphDatabase
from . import constants
from django.shortcuts import render

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))

def search(request, coin=None):
	if coin is None:
		coin = 'usdt'
	
	x = []
	#print('here')
	with driver.session() as session:
		results = session.run("MATCH (a:" + coin.upper() + ") WHERE a.minTx IS NOT NULL RETURN a.name")
		for record in results:
			temp = {
				'addr': record['a.name'],
				'url': "/{}/search/{}".format(coin, record['a.name'])
			}
			x.append(temp)
		#print(x)
		
	search = {'search': x, 'coin': coin, 'homeUrl': '/{}/search/0'.format(coin)}
	return render(request, 'tracker/index.html', search)

def usdt_home(request):
	return search(request, 'usdt')

def btc_home(request):
	return search(request, 'btc')

def home(request):
	return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'homeUrl': '#'})