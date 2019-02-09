from django.db import models
from . import constants
from neo4j.v1 import GraphDatabase
import requests
import json
import time
from datetime import date
import time

usdtUrl = "https://api.omniwallet.org/v1/address/addr/details/"
driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))

def subtract_years(d, years):
    """Return a date that's `years` years after the date (or datetime)
    object `d`. Return the same calendar date (month and day) in the
    destination year, if it exists, otherwise use the following day
    (thus changing February 29 to March 1).
    """
    try:
        return d.replace(year = d.year - years)
    except ValueError:
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

def usdtRequest(addr, page):
	try: 
		print('Checking ' + addr + ' Page: ' + str(page))
		obj = (requests.post(usdtUrl, data = {'addr': addr, 'page': page})).json()
		return obj
	except Exception as e:
		print(e)
		return None

class Node(models.Model):
    name = models.CharField(max_length=250)
    USDT_Address = models.CharField(max_length=250)
    minTx = models.IntegerField(default=1000000)
    tx_Since = models.DateField(default=subtract_years(date.today(), 1))

    def save(self, force_insert=False, force_update=False):
        addrObj = {
            'addr': self.USDT_Address,
            'name': self.name,
            'minTx': self.minTx,
            'tx_since': time.mktime(time.strptime(self.tx_Since.strftime("%yyyy-%mm-%dd"), "%yyyy-%mm-%dd"))
        }
        obj = usdtRequest(addrObj['addr'], 1)
        if obj is None or ('error' in obj['balance'][0] and obj['balance'][0]['error']):
            print("{} Does Not Exist".format(addrObj['addr']))
            return "Error Getting {}".format(addrObj['addr'])
        with driver.session() as session:
            session.run("MERGE (a:USDT {addr:$addr}) "
                        "ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.tx_since = {tx_since}, a.epoch = 0 "
                        "ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.tx_since = {tx_since}, a.epoch = 0 ", 
                        name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], tx_since = addrObj['tx_since'])
            print("Successfully Added USDT Node {}".format(addrObj['name']))
        super(Node, self).save(force_insert, force_update)

    def delete(self, keep_parents=False, allNodes=False):
        with driver.session() as session:
            if not allNodes:
                session.run("MATCH (a:USDT {addr:$addr}) "
                            "DETACH DELETE a ", addr = self.USDT_Address)
                print("Successfully Deleted USDT Node {}".format(self.name))
                super(Node, self).delete(keep_parents)
            else: 
                session.run("MATCH (a:USDT) "
                            "DETACH DELETE a")
                print("Successfully Deleted All USDT Nodes")

    def __str__(self):
        return self.name + ' - ' + self.USDT_Address