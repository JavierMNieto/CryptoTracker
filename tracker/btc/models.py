from django.db import models
from django.core.validators import RegexValidator
from . import constants
from neo4j.v1 import GraphDatabase
import requests
import json
import time
from datetime import date
from lxml import html
import time

btcUrl = "https://blockchain.info/rawaddr/"
driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))
satoshi = constants.satoshi
search  = constants.Search(btcUrl, driver)
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

class Node(models.Model):
    name = models.CharField(max_length=36, validators=[alphanumeric])
    BTC_Address = models.CharField(max_length=36, validators=[alphanumeric])
    minTx = models.FloatField(default=250.00)
    tx_Since = models.DateField(default=subtract_years(date.today(), 1))
    category = models.CharField(max_length=36, validators=[alphanumeric], default='')

    def save(self, force_insert=False, force_update=False):
        if self.category.lower() == 'home':
            return
        if self.pk is None:
            with driver.session() as session:
                addr = session.run("MATCH (a:BTC {addr:$addr}) WHERE a.minTx IS NOT NULL RETURN a LIMIT 1", addr = self.BTC_Address)
                addr = addr.single()
                if addr is not None:
                    print("{} Already Exists!".format(self.BTC_Address))
                    return
        addrObj = {
            'addr': self.BTC_Address,
            'name': self.name,
            'minTx': self.minTx,
            'tx_since': time.mktime(time.strptime(self.tx_Since.strftime("%yyyy-%mm-%dd"), "%yyyy-%mm-%dd")),
            'lastTxTime': 0.0,
            'type': 'BTC',
            'txs': []
        }
        try:
            obj = requests.get(btcUrl + addrObj['addr']).json()
        except Exception as e:
            print(e)
            obj = None
        if obj is None or 'address' not in obj:
            print("{} Does Not Exist".format(addrObj['addr']))
            return
        
        wallet = ''
        try:
            wallet = (requests.get("https://www.walletexplorer.com/address/" + addrObj['addr'])) # get page
            wallet = html.fromstring(wallet.content) # get html
            wallet = wallet.xpath('//div[@class="walletnote"]//a')[0].get('href') # get wallet text
            wallet = wallet.replace('/wallet/', '')

            walletName = (requests.get("https://bitinfocharts.com/bitcoin/address/" + addrObj['addr'])) # get page
            walletName = html.fromstring(walletName.content) # get html
            walletName = walletName.xpath('//table[@class="table table-striped table-condensed"]//a')
            if walletName is None or len(walletName) < 1:
                walletName = wallet
            else:
                walletName = walletName[0].get('href') # get wallet text
                walletName = walletName.replace('../wallet/', '')
        except Exception as e:
            print(e)
            wallet = ''
            print("{} Does Not Belong to a BTC Wallet".format(addrObj['addr']))

        with driver.session() as session:
            session.run("MERGE (a:BTC {addr:$addr}) "
                        "ON CREATE SET a.minTx = {minTx}, a.name = {name}, a.tx_since = {tx_since}, a.wallet = {wallet}, a.walletName = {walletName}, a.epoch = 0, a.balance = {balance} "
                        "ON MATCH SET a.minTx  = {minTx}, a.name = {name}, a.tx_since = {tx_since}, a.epoch = 0, a.balance = {balance}", 
                        name = addrObj['name'], addr = addrObj['addr'], minTx = addrObj['minTx'], tx_since = addrObj['tx_since'], wallet = wallet, walletName = walletName, balance = float(obj['final_balance']/satoshi))
            print("Successfully Added BTC Node {}".format(addrObj['name']))
        super(Node, self).save(force_insert, force_update)

    def delete(self, keep_parents=False, allNodes=False):
        with driver.session() as session:
            if not allNodes:
                session.run("MATCH (a:BTC {addr:$addr}) "
                            "DETACH DELETE a ", addr = self.BTC_Address)
                print("Successfully Deleted BTC Node {}".format(self.name))
                super(Node, self).delete(keep_parents)
            else:
                session.run("MATCH (a:BTC) "
                            "DETACH DELETE a")
                print("Successfully Deleted All BTC Nodes")

    def refresh(self):
        addrObj = {
            'addr': self.BTC_Address,
            'name': self.name,
            'minTx': self.minTx,
            'tx_since': time.mktime(time.strptime(self.tx_Since.strftime("%yyyy-%mm-%dd"), "%yyyy-%mm-%dd")),
            'lastTxTime': 0.0,
            'type': 'BTC',
            'txs': []
        }
        search.threadsBTC(addrObj)

    def __str__(self):
        return self.name + ' - ' + self.BTC_Address