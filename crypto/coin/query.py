from neo4j import GraphDatabase
from django.http import Http404
import json
import time
import re
import os
import sys

sys.path.append("../")
from static.py.clean import *
from static.py.defaults import *

class CoinController:
    driver = GraphDatabase.driver(Neo4j()['url'], auth=(Neo4j()['user'], Neo4j()['pass']))

    def __init__(self):
        pass
    
    def runFilters(self, query, filters=Filters.dFilters):
        query = self.cleanQuery(query, filters)
        return self.driver.session().run(query, minBal=filters['minBal'], maxBal=filters['maxBal'], minTx=filters['minTx'], maxTx=filters['maxTx'],
                                        minTime=filters['minTime'], maxTime=filters['maxTime'], minTotal=filters['minTotal'], maxTotal=filters['maxTotal'],
                                        minTxsNum=filters['minTxsNum'], maxTxsNum=filters['maxTxsNum'], minAvg=filters['minAvg'], maxAvg=filters['maxAvg'])

    def cleanQuery(self, query, filters=Filters.dFilters):
        dFilters = Filters.dFilters
        query = " ".join(query.split())

        for f, val in dFilters.items():
            if f not in filters or filters[f] == val:
                clearFilter = ""

                if "Bal" in f:
                    clearFilter += ".balance"
                elif "Txs" in f:
                    clearFilter += ".txsNum"
                elif "Tx" in f:
                    clearFilter += ".amount"
                elif "Time" in f:
                    clearFilter += ".blocktime"
                elif "Total" in f:
                    clearFilter += ".amount"
                elif "Avg" in f:
                    clearFilter += ".avgTxAmt"
                
                if "min" in f:
                    clearFilter += " >= "
                elif "max" in f:
                    clearFilter += " <= "
                
                if clearFilter != "" and clearFilter in query:
                    clearFilter += "{" + f + "}"

                    nodeNames = ["r"]

                    if "Bal" in f:
                        nodeNames = ["a", "b"]
                    
                    for name in nodeNames:
                        tempClear = name + clearFilter

                        if "AND " + tempClear in query:
                            tempClear = "AND " + tempClear
                        
                        query = query.replace(tempClear, "", 1)

        query = " ".join(query.split())

        if "CASE WHEN THEN" in query:
            query = query.replace(" {amount: SUM(r.amount),txsNum: count(r),avgTxAmt: SUM(r.amount)/count(r)} as r, COLLECT(r) as txs WITH CASE WHEN THEN REDUCE(vals = [], tx in txs | vals + [{from: a, to: b, txid: tx.txid, amount: tx.amount, blocktime: tx.blocktime, type: TYPE(tx), id: ID(tx)}]) ELSE NULL END AS result UNWIND result", 
                                " r WITH {from: a, to: b, txid: r.txid, amount: r.amount, blocktime: r.blocktime, type: TYPE(r), id: ID(r)}")
            query = query.replace("CASE WHEN THEN", "")
            query = query.replace("ELSE NULL END", "")

        return query

    def getTxs(self, session, params=DParams(), filters=DFilters()):
        query = (TxsQuery() + "RETURN r ORDER BY r." + params['sort'] + " " + params['order'] + " SKIP " + str(int(params['page']*TxsPerPage())) + " LIMIT " + str(TxsPerPage()))

        addrsText = ''

        if params['addr[]']:
            addrsText = "({}) AND".format(self.getAddrsText(params['addr[]']))

            query     = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {} {}".format(session.coin.name, session.coin, session.coin.name, addrsText, query)
        elif params['sender[]'] and params['receiver[]']:
            addrsText = "{} AND".format(self.getAddrsText(params['sender[]'], params['receiver[]'], rel=False))
            query     = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {} {}".format(session.coin.name, session.coin.name, session.coin.name, addrsText, query.replace("WITH startNode(r) as a, endNode(r) as b, r ", ""))
        else:
            raise Http404("Address(es) required!")
            #query = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {}".format(self.coin, self.coin, self.coin, query)

        txs = self.runFilters(query, filters)

        edges = []

        for tx in txs:
            rel = tx.get('r')
            aNode = rel['from']
            bNode = rel['to']

            rel = {
                "from": aNode['id'],
                "to": bNode['id'],
                #"id": rel['id'],
                "value": float(rel['amount']),
                "source": self.getNodeFromSession(session, aNode['addr'])['name'],
                "sourceAddr": aNode['addr'],
                "target": self.getNodeFromSession(session, bNode['addr'])['name'],
                "targetAddr": bNode['addr'],
                "type": rel['type'],
                #"amount": float(rel['amount']),
                "time": rel['blocktime'],
                "txid": rel['txid'],
                "img": session.coin.getImg(),
                "txidUrl": session.coin.getUrl() + "/getTx/" + rel['txid'],
                "sourceUrl": session.getUrl() + "/addr/" + aNode['addr'],
                "targetUrl": session.getUrl() + "/addr/" + bNode['addr']
            }
            edges.append(rel)

        return edges

    def getNodeFromSession(self, session, addr):
        try:
            node = session.getNode(addr)
            return {
                "name": node.name,
                "addr": node.addr,
                "url": node.getUrl()
            }
        except Http404 as e:
            pass

        return {"name": addr, "addr": addr, "url": session.getUrl() + "/addr/" + addr}

    def getAddr(self, addr, session, filters):
        info = {
            "session": session.name,
            "label": addr,
            "addr": addr,
            "totalTxs": 0,
            "balance": 0,
            "filters": {}
        }

        try:
            info["label"] = session.getNode(addr).name
        except Exception as e:
            pass
        
        node = self.driver.session().run("MATCH (a:" + session.coin.name + ") WHERE a.addr = {addr} RETURN a", addr=addr).single()
        
        if node:
            node = node.value()
        else:
            info['addr'] = [addr + " DOES NOT EXIST"]
            return {"search": info}

        info['addr']    = node['addr']
        info['balance'] = node['balance']

        info['url']  = session.getUrl() + "/addr/" + info['addr']
        info['addr'] = [info['addr']]
        info['totalTxs'] = self.getNumTxs(session.coin.name, info['addr'], filters)
        
        info['dFilters'] = Filters.dFilters

        info['filters']  = Filters(filters).getFormattedFilters()

        return info

    def getGroup(self, session, filters, group_id=None, addrs=None):   
        info = {
            "label": "Custom Graph",
            "addr": [],
            "totalTxs": 0,
            "balance": 0,
            "filters": {}
        }

        if group_id:
            group = session.getGroup(group_id)
            info['label'] = group.name
            info['addr']  = group.getAddrs()
        elif addrs:
            info['addr'] = addrs
            info['names'] = []

            for addr in addrs:
                try:
                    node = session.getNode(addr)
                    info['names'].append(node.name)
                except Http404 as e:
                    info['names'].append(addr)
        else:
            raise Http404("Invalid Group!")
        
        info['balance']  = self.driver.session().run("MATCH (a: " + session.coin.name + ") WHERE " + self.getAddrsText(info['addr'], rel=False) + " RETURN SUM(a.balance)").single().value()

        info["totalTxs"] = self.getNumTxs(session.coin.name, info['addr'], filters)
        
        info['dFilters'] = Filters.dFilters

        info['filters']  = Filters(filters).getFormattedFilters()

        return {
            "session": session.name,
            **info
        }
    
    def getNumTxs(self, coin, addrs, filters):
        addrText = ""

        if addrs:
            addrText = self.getAddrsText(addrs) + " AND "

        query  = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {} {} RETURN count(r)".format(coin, coin, coin, addrText, TxsQuery())

        return self.runFilters(query, filters).single().value()


    def getGraphData(self, session, params, filters, lastId=0):
        query = GraphQuery()
        
        if isInt(lastId):
            lastId = int(lastId)
        else:
            lastId = 0

        addrsText = ''

        data = {
            'nodes': [],
            'edges': [],
            'totalTxs': 0
        }

        if params['addr[]']:
            """
            for addr in params['addr[]']:
                if not self.isValidAddr(addr):
                    return data
            """

            addrsText = "({}) AND".format(self.getAddrsText(params['addr[]']))

        query = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {} {}".format(session.coin.name, session.coin.name, session.coin.name, addrsText, query)

        txs   = self.runFilters(query, filters)

        id = lastId

        for nodes in txs:
            nodes = nodes.get('result')
            if nodes:
                aNode = nodes['from']
                aKnown = self.getNodeFromSession(session, aNode['addr'])
                aNode = {
                    "id": aNode.id,
                    "label": aKnown['name'],
                    "addr": aNode['addr'],
                    #"balance": float(aNode['balance'] or 0),
                    #"balVal": float(aNode['balance'] or 0),
                    "group": 'usdt' if lastId == 0 else 'tempusdt', #aNode['wallet'] or 
                    "url": aKnown['url'],
                    "value": float(aNode['balance'] or 0),#/Satoshi(),
                    "img": session.coin.getImg(),
                    "title": ("Address: {}<br> "
                            "Balance: ${} ").format(aNode['addr'], numWithCommas(aNode['balance'] or "0", dec=3))
                }
                if aNode['label'] != aNode['addr']:
                    aNode['title'] = "Name: {}<br>".format(aNode['label']) + aNode['title']

                if params['addr[]'] and not inArr(params['addr[]'], aNode['addr']):
                    aNode['title'] += "<br> <b>Double Click to Load Transactions!</b>"
                
                bNode  = nodes['to']
                bKnown = self.getNodeFromSession(session, bNode['addr'])
                bNode = {
                    "id": bNode.id,
                    "label": bKnown['name'],
                    "addr": bNode['addr'],
                    #"balance": float(bNode['balance'] or 0),
                    #"balVal": float(bNode['balance'] or 0),
                    "group": 'usdt' if lastId == 0 else 'tempusdt', #bNode['wallet'] or 
                    "url": bKnown['url'],
                    "value": float(bNode['balance'] or 0),#/Satoshi(),
                    "img": session.coin.getImg(),
                    "title": ("Address: {}<br> "
                            "Balance: ${} ").format(bNode['addr'], numWithCommas(bNode['balance'] or "0", dec=3))
                }
                if bNode['label'] != bNode['addr']:
                    bNode['title'] = "Name: {}<br>".format(bNode['label']) + bNode['title']
                
                if params['addr[]'] and not inArr(params['addr[]'], bNode['addr']):
                    bNode['title'] += "<br> <b>Double Click to Load Transactions!</b>"

                rel = nodes['r']
                id += 1
                rel = {
                    "from": aNode['id'],
                    "to": bNode['id'],
                    "id": id,
                    "value": float(rel['amount'] or 0),
                    "source": aNode['label'],
                    "target": bNode['label'],
                    "sourceAddr": aNode['addr'],
                    "targetAddr": bNode['addr'],
                    #"amount": float(rel['amount'] or 0),
                    "txsNum": int(rel['txsNum'] or 1.0),
                    "avgTx": float(rel['avgTxAmt'] or rel['amount'] or 0),
                    "img": session.coin.getImg(),
                    "color": {
                        "color": "#26A17B" if lastId == 0 else "#AEB6BF"
                    },
                    "sourceUrl": session.getUrl() + "/addr/" + aNode['addr'],
                    "targetUrl": session.getUrl() + "/addr/" + bNode['addr']
                }
                rel['title'] = ("# of Txs: {}<br> "
                                "Total: ${}<br> "
                                "Average Tx Amount: ${}<br>").format(numWithCommas(rel['txsNum'], dec=3), numWithCommas(rel['value'], dec=3), numWithCommas(rel['avgTx'], dec=3))
                data['totalTxs'] += rel['txsNum']
                
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
                    data['nodes'].append(aNode)
                if not bExists:
                    data['nodes'].append(bNode)
                data['edges'].append(rel)
        
        return data
        
    def getAddrsText(self, addr, extras=[], rel=True):
        addrsText = ""
        for x in range(len(addr)):
            string = ""

            if "!" in addr[x]:
                string += "NOT (a.addr = '{}') AND NOT (b.addr='{}')".format(addr[x].replace("!", ""), addr[x].replace("!", ""))
            else:
                string += "a.addr = '{}'".format(addr[x])

                """
                if rel:
                    string = "({} OR b.addr = '{}')".format(string, addr[x])
                """

            if x < len(extras):
                string = "(({}) AND (b.addr = '{}'))".format(string, extras[x])

            if addrsText != "":
                if "NOT" in string:
                    string = " AND " + string
                else:
                    string = " OR " + string

            addrsText += string

        return "({})".format(addrsText)

    def isValidAddr(self, coin, addr):
        if len(addr) == 34 and ' ' not in addr and re.match(r'^[A-Za-z0-9]*$', addr):
            node = self.driver.session().run("MATCH (a:" + coin.upper() + ") WHERE a.addr = '" + addr + "' RETURN a.addr").single()

            if node:
                return True
        return False