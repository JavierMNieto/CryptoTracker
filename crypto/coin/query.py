from neo4j import GraphDatabase
from django.http import Http404
from .clean import *
from .defaults import *
from .utils import is_numeric
import json
import time
import re
import os
import sys

"""
    Handles filtering and formatting transactions
"""
class CoinController:
    driver = GraphDatabase.driver(Neo4j()['url'], auth=(Neo4j()['user'], Neo4j()['pass']))
    
    """
        Pass filters into query for neo4j
    """
    def run_filters(self, query, filters=Filters.dFilters):
        query = self.clean_query(query, filters) 
        return self.driver.session().run(query, minBal=filters['minBal'], maxBal=filters['maxBal'], minTx=filters['minTx'], maxTx=filters['maxTx'],
                                        minTime=filters['minTime'], maxTime=filters['maxTime'], minTotal=filters['minTotal'], maxTotal=filters['maxTotal'],
                                        minTxsNum=filters['minTxsNum'], maxTxsNum=filters['maxTxsNum'], minAvg=filters['minAvg'], maxAvg=filters['maxAvg'])

    """
        Cleans query to ensure most efficient query is to be executed
        (e.g. No need to filter balance if user does not give value to filter)
        TODO: Change whole query forming process to not have to split up string 
        (Juli, if you find a different way pls tell how you did it)
    """
    def clean_query(self, query, filters=Filters.dFilters):
        dFilters = Filters.dFilters
        query = " ".join(query.split())

        for f, val in dFilters.items():
            # Take out filters not specified by user or filters that are min or max
            if f not in filters or filters[f] == val:
                # String to eventually remove from query
                clear_filter = ""

                if "Bal" in f:
                    clear_filter += ".balance"
                elif "Txs" in f:
                    clear_filter += ".txsNum"
                elif "Tx" in f:
                    clear_filter += ".amount"
                elif "Time" in f:
                    clear_filter += ".blocktime"
                elif "Total" in f:
                    clear_filter += ".amount"
                elif "Avg" in f:
                    clear_filter += ".avgTxAmt"
                
                if "min" in f:
                    clear_filter += " >= "
                elif "max" in f:
                    clear_filter += " <= "
                
                if clear_filter != "" and clear_filter in query:
                    clear_filter += "{" + f + "}"

                    # Determine if filter is node or relationship 
                    # (I know it's bad since it relies on rel and node to be specific characters)
                    node_names = ["r"]
                    if "Bal" in f:
                        node_names = ["a", "b"]
                    
                    for name in node_names:
                        temp_clear = name + clear_filter

                        if "AND " + temp_clear in query:
                            temp_clear = "AND " + temp_clear
                        
                        query = query.replace(temp_clear, "", 1)

        query = " ".join(query.split())

        # If there are no filters then there is no need to group up txs to filter them
        if "CASE WHEN THEN" in query:
            query = query.replace(" {amount: SUM(r.amount),txsNum: count(r),avgTxAmt: SUM(r.amount)/count(r)} as r, COLLECT(r) as txs WITH CASE WHEN THEN REDUCE(vals = [], tx in txs | vals + [{from: a, to: b, txid: tx.txid, amount: tx.amount, blocktime: tx.blocktime, type: TYPE(tx), id: ID(tx)}]) ELSE NULL END AS result UNWIND result", 
                                " r WITH {from: a, to: b, txid: r.txid, amount: r.amount, blocktime: r.blocktime, type: TYPE(r), id: ID(r)}")
            query = query.replace("CASE WHEN THEN", "")
            query = query.replace("ELSE NULL END", "")

        return query

    """
        Gets individual filtered transactions and formats them
    """
    def get_txs(self, session, params=DParams(), filters=DFilters()):
        # Setup query with specifc page and sorting type
        query = (TxsQuery() + "RETURN r ORDER BY r." + params['sort'] + " " + params['order'] + " SKIP " + str(int(params['page']*TxsPerPage())) + " LIMIT " + str(TxsPerPage()))

        # Format of addresses to get transactions of
        addrs_text = ''

        # Determine if query is of addresses or specific senders and receivers
        if params['addr[]']:
            addrs_text = "({}) AND".format(self.get_addrs_text(params['addr[]']))
            query     = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {} {}".format(session.coin.name, session.coin, session.coin.name, addrs_text, query)
        elif params['sender[]'] and params['receiver[]']:
            addrs_text = "{} AND".format(self.get_addrs_text(params['sender[]'], params['receiver[]'], rel=False))
            query     = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {} {}".format(session.coin.name, session.coin.name, session.coin.name, addrs_text, query.replace("WITH startNode(r) as a, endNode(r) as b, r ", ""))
        else:
            raise Http404("Address(es) required!")
            # Maybe get all txs with this but may be to much processing 
            # query = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {}".format(self.coin, self.coin, self.coin, query)

        txs = self.run_filters(query, filters)

        # Format txs into edges for frontend
        edges = []
        for tx in txs:
            rel = tx.get('r')
            a_node = rel['from']
            b_node = rel['to']

            rel = {
                "from": a_node['id'],
                "to": b_node['id'],
                #"id": rel['id'],
                "value": float(rel['amount']), # TODO: Maybe add usd value for mixing different coins in graphs
                "source": self.get_node_from_session(session, a_node['addr'])['name'],
                "sourceAddr": a_node['addr'],
                "target": self.get_node_from_session(session, b_node['addr'])['name'],
                "targetAddr": b_node['addr'],
                "type": rel['type'],
                #"amount": float(rel['amount']),
                "time": rel['blocktime'],
                "txid": rel['txid'],
                "img": session.coin.get_img(),
                "txidUrl": session.coin.get_url() + "/getTx/" + rel['txid'],
                "sourceUrl": session.get_url() + "/addr/" + a_node['addr'],
                "targetUrl": session.get_url() + "/addr/" + b_node['addr']
            }
            edges.append(rel)

        return edges

    """
        Format node with user's label if it exists in user's session
    """
    def get_node_from_session(self, session, addr):
        try:
            node = session.get_node(addr)
            return {
                "name": node.name,
                "addr": node.addr,
                "url": node.get_url()
            }
        except Http404:
            return {
                "name": addr, 
                "addr": addr, 
                "url": session.get_url() + "/addr/" + addr
            }

    """
        Get specific node/address info from database
    """
    def get_addr(self, addr, session, filters):
        info = {
            "session": session.name,
            "label": addr,
            "addr": addr,
            "totalTxs": 0,
            "balance": 0,
            "filters": {}
        }

        try:
            info["label"] = session.get_node(addr).name
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
        info['is_frozen'] = node['is_frozen']

        info['url']  = session.get_url() + "/addr/" + info['addr']
        info['addr'] = [info['addr']]
        info['totalTxs'] = self.get_num_txs(session.coin.name, info['addr'], filters)
        
        info['dFilters'] = Filters.dFilters

        info['filters']  = Filters(filters).get_formatted_filters()

        return info

    """
        Get group in user's session or that is custom created
    """
    def get_group(self, session, filters, group_id=None, addrs=None):   
        info = {
            "label": "Custom Graph",
            "addr": [],
            "totalTxs": 0,
            "balance": 0,
            "filters": {}
        }

        if group_id:
            group = session.get_group(group_id)
            info['label'] = group.name
            info['addr']  = group.get_addrs()
        elif addrs:
            info['addr'] = addrs
            info['names'] = []

            for addr in addrs:
                try:
                    node = session.get_node(addr)
                    info['names'].append(node.name)
                except Http404 as e:
                    info['names'].append(addr)
        else:
            raise Http404("Invalid Group!")
        
        info['balance']  = self.driver.session().run("MATCH (a: " + session.coin.name + ") WHERE " + self.get_addrs_text(info['addr'], rel=False) + " RETURN SUM(a.balance)").single().value()
        info["totalTxs"] = self.get_num_txs(session.coin.name, info['addr'], filters)
        info['dFilters'] = Filters.dFilters
        info['filters']  = Filters(filters).get_formatted_filters()

        return {
            "session": session.name,
            **info
        }
    
    """
        Gets number of txs from address(es)
    """
    def get_num_txs(self, coin, addrs, filters):
        addrText = ""

        if addrs:
            addrText = self.get_addrs_text(addrs) + " AND "

        query  = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {} {} RETURN count(r)".format(coin, coin, coin, addrText, TxsQuery())

        return self.run_filters(query, filters).single().value()

    """
        Gets filtered txs for graph and formats them for vis.js
    """
    def get_graph_data(self, session, params, filters, last_id=0):
        query = GraphQuery()
        
        # Get last id of tx if adding txs to existing graph
        if is_numeric(last_id):
            last_id = int(last_id)
        else:
            last_id = 0

        addrs_text = ''

        data = {
            'nodes': [],
            'edges': [],
            'totalTxs': 0
        }
        if params['addr[]']:
            """
            for addr in params['addr[]']:
                if not self.is_valid_addr(addr):
                    return data
            """

            addrs_text = "({}) AND".format(self.get_addrs_text(params['addr[]']))

        query = "MATCH (a:{})-[r:{}TX]-(b:{}) WHERE {} {}".format(session.coin.name, session.coin.name, session.coin.name, addrs_text, query)

        txs   = self.run_filters(query, filters)
        id = last_id

        for nodes in txs:
            nodes = nodes.get('result')
            if nodes:
                a_node = nodes['from']
                a_known = self.get_node_from_session(session, a_node['addr'])

                group = "usdt"

                if a_node['addr'] in params['addr[]']:
                    group = "main"
                elif last_id != 0:
                    group = "tempusdt"

                a_node = {
                    "id": a_node.id,
                    "label": a_known['name'],
                    "addr": a_node['addr'],
                    #"balance": float(a_node['balance'] or 0),
                    #"balVal": float(a_node['balance'] or 0), maybe for mixing different coins in the same grapoh
                    "group": group, #a_node['wallet'] or 
                    "url": a_known['url'],
                    "value": float(a_node['balance'] or 0), #/Satoshi(),
                    "img": session.coin.get_img(),
                    "title": ("Address: {}<br> "
                            "Balance: ${} ").format(a_node['addr'], num_with_commas(a_node['balance'] or "0", dec=3))
                }
                if a_node['label'] != a_node['addr']:
                    a_node['title'] = "Name: {}<br>".format(a_node['label']) + a_node['title']

                if params['addr[]'] and not in_arr(params['addr[]'], a_node['addr']):
                    a_node['title'] += "<br> <b>Double Click to Load Transactions!</b>"
                
                b_node  = nodes['to']
                b_known = self.get_node_from_session(session, b_node['addr'])

                group = "usdt"

                if b_node['addr'] in params['addr[]']:
                    group = "main"
                elif last_id != 0:
                    group = "tempusdt"

                b_node = {
                    "id": b_node.id,
                    "label": b_known['name'],
                    "addr": b_node['addr'],
                    #"balance": float(b_node['balance'] or 0),
                    #"balVal": float(b_node['balance'] or 0),
                    "group": group, #b_node['wallet'] or 
                    "url": b_known['url'],
                    "value": float(b_node['balance'] or 0),#/Satoshi(),
                    "img": session.coin.get_img(),
                    "title": ("Address: {}<br> "
                            "Balance: ${} ").format(b_node['addr'], num_with_commas(b_node['balance'] or "0", dec=3))
                }
                if b_node['label'] != b_node['addr']:
                    b_node['title'] = "Name: {}<br>".format(b_node['label']) + b_node['title']
                
                if params['addr[]'] and not in_arr(params['addr[]'], b_node['addr']):
                    b_node['title'] += "<br> <b>Double Click to Load Transactions!</b>"

                rel = nodes['r']
                id += 1
                rel = {
                    "from": a_node['id'],
                    "to": b_node['id'],
                    "id": id,
                    "value": float(rel['amount'] or 0),
                    "source": a_node['label'],
                    "target": b_node['label'],
                    "sourceAddr": a_node['addr'],
                    "targetAddr": b_node['addr'],
                    #"amount": float(rel['amount'] or 0),
                    "txsNum": int(rel['txsNum'] or 1.0),
                    "avgTx": float(rel['avgTxAmt'] or rel['amount'] or 0),
                    "img": session.coin.get_img(),
                    "color": {
                        "color": "#26A17B" if last_id == 0 else "#AEB6BF"
                    },
                    "sourceUrl": session.get_url() + "/addr/" + a_node['addr'],
                    "targetUrl": session.get_url() + "/addr/" + b_node['addr']
                }
                rel['title'] = ("# of Txs: {}<br> "
                                "Total: ${}<br> "
                                "Average Tx Amount: ${}<br>").format(num_with_commas(rel['txsNum'], dec=3), num_with_commas(rel['value'], dec=3), num_with_commas(rel['avgTx'], dec=3))
                data['totalTxs'] += rel['txsNum']
                
                # Check if either nodes need to added to list of nodes for graph
                # TODO: find more efficient way to go about this
                a_exists = False
                b_exists = False

                for node in data['nodes']:
                    if node['id'] == a_node['id']:
                        a_exists = True
                    if node['id'] == b_node['id']:
                        b_exists = True
                    if a_exists and b_exists:
                        break
                if not a_exists:
                    data['nodes'].append(a_node)
                if not b_exists:
                    data['nodes'].append(b_node)
                data['edges'].append(rel)
        
        return data
    
    """
        Builds query string of addresses to include for queries
    """
    def get_addrs_text(self, addr, extras=[], rel=True):
        addrs_text = ""
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

            if addrs_text != "":
                if "NOT" in string:
                    string = " AND " + string
                else:
                    string = " OR " + string

            addrs_text += string

        return "({})".format(addrs_text)

    """
        Checks if address is valid node in database
    """
    def is_valid_addr(self, coin, addr):
        if len(addr) == 34 and ' ' not in addr and re.match(r'^[A-Za-z0-9]*$', addr):
            node = self.driver.session().run("MATCH (a:" + coin.upper() + ") WHERE a.addr = '" + addr + "' RETURN a.addr").single()

            if node:
                return True
        return False