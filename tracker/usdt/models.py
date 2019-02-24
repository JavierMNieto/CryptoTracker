from django.db import models
from django.core.validators import RegexValidator
from . import constants
from neo4j.v1 import GraphDatabase
import requests
import json
import time
from datetime import date
import time

usdtUrl = "https://api.omniwallet.org/v1/address/addr/details/"
driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))
satoshi = constants.satoshi
search  = constants.Search(usdtUrl, driver)
alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

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
    name = models.CharField(max_length=250, validators=[alphanumeric])
    USDT_Address = models.CharField(max_length=250, validators=[alphanumeric])
    minTx = models.FloatField(default=1000000.00)
    tx_Since = models.DateField(default=subtract_years(date.today(), 1))
    category = models.CharField(max_length=36, validators=[alphanumeric], default='', blank=True)

    def save(self, force_insert=False, force_update=False):
        if self.category.lower() == 'home':
            return
        if self.pk is None:
            with driver.session() as session:
                addr = session.run("MATCH (a:USDT {addr:$addr}) WHERE a.minTx IS NOT NULL RETURN a LIMIT 1", addr = self.USDT_Address)
                addr = addr.single()
                if addr is not None:
                    print("{} Already Exists!".format(self.USDT_Address))
                    return
        addrObj = {
            'addr': self.USDT_Address,
            'name': self.name,
            'minTx': self.minTx,
            'tx_since': time.mktime(time.strptime(self.tx_Since.strftime("%yyyy-%mm-%dd"), "%yyyy-%mm-%dd")),
            'lastTxTime': 0,
            'type': 'USDT', 
            'txs': []
        }
        obj = usdtRequest(addrObj['addr'], 1)
        if obj is None or ('error' in obj['balance'][0] and obj['balance'][0]['error']):
            print("{} Does Not Exist".format(addrObj['addr']))
            return
        for coin in obj['balance']:
            if int(coin['id']) == 31:
                balance = float(coin['value'])/satoshi
                break
        with driver.session() as session:
            session.run("MERGE (a:USDT {addr:$addr}) "
                        "ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.tx_since = {tx_since}, a.epoch = 0, a.balance = {balance} "
                        "ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.tx_since = {tx_since}, a.epoch = 0, a.balance = {balance} ", 
                        name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], tx_since = addrObj['tx_since'], balance = balance)
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

    def refresh(self):
        addrObj = {
            'addr': self.USDT_Address,
            'name': self.name,
            'minTx': self.minTx,
            'tx_since': time.mktime(time.strptime(self.tx_Since.strftime("%yyyy-%mm-%dd"), "%yyyy-%mm-%dd")),
            'lastTxTime': 0,
            'type': 'USDT', 
            'txs': []
        }
        search.threadsUSDT(addrObj)

    def __str__(self):
        return self.name + ' - ' + self.USDT_Address