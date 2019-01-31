import requests
import json
import time
import pprint
from urllib.parse import parse_qs as pq
from neo4j import GraphDatabase
from constants import neo4j

# name, addr, maxTime(epoch seconds), minTx Ex: Treasury, 1NTMakcgVwQpMdGxRQnFKyb3G1FAJysSfz, 94670856, 1000000
addrs = [
	#{'name': "Treasury", "addr": "1NTMakcgVwQpMdGxRQnFKyb3G1FAJysSfz", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Binance", "addr": "1FoWyxwPXuj4C6abqwhjDWdz6D4PZgYRjA", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Bitfinex", "addr": "1KYiKJEfdJtap9QX2v9BXJMpz2SfU4pgZw", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Bittrex", "addr": "1DUb2YYbQA1jjaNYzVXLZ7ZioEhLXtbUru", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Huobi-Main", "addr": "168o1kqNquEJeR9vosUB5fw4eAwcVAgh8P", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Huobi", "addr": "12Pch67619NRn3sXKyfsdxrLZ8fCe4Koxh", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Huobi2", "addr": "1LAnF8h3qMGx3TSwNUHVneBZUEpwE4gu3D", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Huobi-Reserve", "addr": "1HckjUpRGcrrRAtFaaCAUaGjsPx9oYmLaZ", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Poloniex", "addr": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Poloniex2", "addr": "1A9AUhKv6aLrKGAdwMM9aHXECZM9uQivZK", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Poloniex3", "addr": "1LJjvsEN9ZzeBVPB4XbhS7mxg99gBAPoMB", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Poloniex4", "addr": "1G6jMfQotd6rV8VkMFNx4hPXYHioeBdquf", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "OKEX", "addr": "37Tm3Qz8Zw2VJrheUUhArDAoq58S6YrS3g", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "Kraken", "addr": "3GyeFJmQynJWd8DeACm4cdEnZcckAtrfcN", "maxTime": 31556952, "minTx": 1000000},
	#{'name': "1GrZG61AoHVn8UZcHiX2gJgAkajRaTo1C3", "addr": "1GrZG61AoHVn8UZcHiX2gJgAkajRaTo1C3", "maxTime": 31556952, "minTx": 1000000}
	#{'name': "3MqkXrq5eb72thzeFDKkaUTwTwB5zB54YH", "addr": "3MqkXrq5eb72thzeFDKkaUTwTwB5zB54YH", "maxTime": 31556952, "minTx": 1000000}
	#{'name': "3MbYQMMmSkC3AgWkj9FMo5LsPTW1zBTwXL", "addr": "3MbYQMMmSkC3AgWkj9FMo5LsPTW1zBTwXL", "maxTime": 31556952, "minTx": 1000000}
	{'name': "1pYbaaWDhezjBkXBHEUqTHCc6DbefSZiK", "addr": "1pYbaaWDhezjBkXBHEUqTHCc6DbefSZiK", "maxTime": 31556952, "minTx": 1000000},
	{'name': "1KQ4DHSvR4zN5ZEQS9SfV71DK5rwm529KG", "addr": "1KQ4DHSvR4zN5ZEQS9SfV71DK5rwm529KG", "maxTime": 31556952, "minTx": 1000000}
]

usdtUrl = "https://api.omniwallet.org/v1/address/addr/details/"
driver = GraphDatabase.driver(neo4j['url'], auth=(neo4j['user'], neo4j['pass']))

def usdtRequest(addr, page):
	try: 
		print('Checking ' + addr + ' Page: ' + str(page))
		obj = (requests.post(usdtUrl, data = {'addr': addr, 'page': page})).json()
		return obj
	except Exception as e:
		print(e)
		return None

def getUSDT(addrObj):
	obj = usdtRequest(addrObj['addr'], 1)
	if obj is None:
		print("Address Does Not Exist")
		return "Error Getting {}".format(addrObj['addr'])
	with driver.session() as session:
		session.run("MERGE (a:USDT {addr:$addr}) "
					"ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.tx_since = {tx_since} "
					"ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.tx_since = {tx_since} ", 
					name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], tx_since = addrObj['maxTime'])

for addr in addrs:
	getUSDT(addr)