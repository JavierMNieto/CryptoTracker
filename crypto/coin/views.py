"""
	Probably worth checking out new angular https://angular.io/ for easy backend and frontend compatibility
    TODO: Maybe use class view instead for more organised url/function mapping
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import TemplateView
from neo4j import GraphDatabase
from django.core.exceptions import ValidationError
from urllib.parse import unquote
from pyvis.network import Network
from .clean import *
from .defaults import *
from .utils import *
from .models import Coin, Session
import pprint
import json
import math
import time
import datetime
import sys
import ccxt
import re
import requests
import traceback

coins = ["USDT"]


def home(request, coin=None):
    btc = None
    #btc = ccxt.coinbase().fetch_ticker('BTC/USD')

    sessions = request.user.get_coin(coin).get_sessions()
    basic_session = Coin.objects.filter(
        name__iexact=coin).first().sessions.first().get_as_dict()
    return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'btc': btc, 'basic_session': basic_session, 'sessions': sessions, 'session': None})


def session(request, coin=None, session_id=None):
    session = request.user.get_coin(coin).get_session(session_id).name

    btc = None
    #btc = ccxt.coinbase().fetch_ticker('BTC/USD')

    search = {'coin': coin, 'btc': btc, 'dFilters': Filters(
    ).get_formatted_filters(), 'session': session}
    return render(request, 'tracker/index.html', search)


def go_to_default_session(request, coin):
    return redirect(Coin.objects.filter(name__iexact=coin).first().sessions.first().get_url())


def get_known(request, coin=None, session_id=None):
    return JsonResponse(request.user.get_coin(coin).get_session(session_id).get_as_list(), safe=False)


def add(req_data, session):
    group = req_data.get("cat", "")

    group = session.add_group(group)

    return group.add_node(req_data.get("name", ""), req_data.get("addr", ""), get_filters(req_data, format=False))


def delete(req_data, session):
    group = session.get_group(req_data.get("prevCat", ""))

    return group.del_node(req_data.get("addr", ""))


def edit(req_data, session):
    delete(req_data, session)
    add(req_data, session)

    return "Successfully edited node."


def edit_cat(req_data, session):
    group = session.get_group(req_data.get("cat", ""))
    if group.name != req_data.get("newCat", ""):
        group.setName(req_data.get("newCat", ""))

    group.set_filters(get_filters(req_data, format=False),)

    return "Successfully edited group."


methods = {
    "add": add,
    "delete": delete,
    "edit": edit,
    "editCat": edit_cat
}


def change(request, coin=None, session_id=None):
    if request.method != "POST":
        raise Http404('Only POSTs are allowed!')

    method = request.POST.get('method', '')

    resp = "ERROR"

    try:
        if method in methods:
            resp = methods[method](request.POST, request.user.get_coin(
                coin).get_session(session_id))
    except ValidationError as e:
        resp = "ERROR! " + e.message
    except Exception as e:
        print(e)

    return JsonResponse(resp, safe=False)


def get_tx(request, tx, coin=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")

    if request.GET.get("rawTx"):
        return JsonResponse(get_blockchain("omni_gettransaction", [tx]), json_dumps_params={'indent': 2})
    return render(request, 'coin/tx.html', get_blockchain("omni_gettransaction", [tx]))


def is_uniq_session(request, coin=None):
    uniq = True

    try:
        request.user.get_coin(coin).is_uniq_session(request.GET.get("name"))
    except ValidationError as e:
        uniq = False

    return JsonResponse(uniq, safe=False)


def copy_session(request, coin=None, session_id=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        session = request.user.get_coin(coin).add_session(
            request.POST.get("name", ""), copy_session=session_id)

        if session:
            return JsonResponse(session.get_url(), safe=False)

    return JsonResponse("ERROR", safe=False)


def add_session(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        session = request.user.get_coin(coin).add_session(
            request.POST.get("name", ""))

        if session:
            return JsonResponse(session.get_url(), safe=False)

    return JsonResponse("ERROR", safe=False)


def del_session(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        return JsonResponse(request.user.get_coin(coin).del_session(request.POST.get("session_id", "")), safe=False)

    return JsonResponse("ERROR", safe=False)


def edit_session(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        return JsonResponse(request.user.get_coin(coin).edit_session(request.POST.get("session_id", ""), request.POST.get("name", "")), safe=False)

    return JsonResponse("ERROR", safe=False)


"""
    TODO: Better Filter Efficiency by only adding custom filters instead of replacing defaults
"""


def get_filters(req_data, format=True):
    filters = DFilters()
    for f, val in filters.items():
        temp = req_data.get(f)

        if temp and temp != "max" and temp != "latest" and temp != "min" and temp != "oldest":
            try:
                temp = float(temp.replace(" ", ""))
            except Exception:
                if "max" in f or "min" in f:
                    continue

            filters[f] = temp

    if format:
        return Filters(filters).get_raw_filters()

    return filters


"""
conversionToHours = {
    "second": 1/3600,
    "minute": 1/60,
    "hour": 1,
    "day": 24,
    "week": 7*24,
    "month": 30*24,
    "year": 365*24
}

def convertToHours(amt, time):
    for t, val in conversionToHours.items():
        if t in time:
            return amt*val
    
    return 0

def parseTimeRange(range):
    amt = int(re.search(r'\d+', range).group())
    hours = convertToHours(amt, range.lower())

    return -datetime.timedelta(hours=hours).total_seconds()
"""


def get_params(req_data):
    params = DParams()
    for p, val in params.items():
        temp = None

        if '[]' in p:
            temp = req_data.getlist(p)
        else:
            temp = req_data.get(p)

        if temp:
            try:
                temp = float(temp.replace(" ", ""))
                if p == 'page':
                    temp = max(int(temp), 0)
            except Exception:
                if p == "page":
                    continue

            if ("order" in p.lower() and val.lower() != "desc" and val.lower() != "asc") or ("sort" in p.lower() and val.lower() != "blocktime" and val.lower() != "amount" and val.lower() != "usdAmount"):
                continue

            params[p] = temp

    return params


def get_blockchain(method, params=[]):
    """Return info from directly blockchain"""

    data = {"method": method, "params": params, "jsonrpc": "1.0"}
    return (requests.post("http://127.0.0.1:8332/", auth=Auth(), data=json.dumps(data), headers={'content-type': 'application/json'}).json())['result']


class ValidAddressView(QueryMixin, View):
    """View for determining whether an address is 
    valid in the neo4j database."""
    
    def get_context_data(self, **kwargs):
        """Check if address is valid from neo4j 
        and return boolean as response data."""
        
        self.kwargs["coin"] = self.kwargs["coin"].upper()
        return self.is_valid_addr(self.request.GET.get("addr", ""))

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Return response as JSON."""
        
        return JsonResponse(self.get_context_data(), safe=False)


class ExplorerView(QueryMixin, TemplateView):
    """View for processing requests getting the explorer 
    page of an address or a group of addresses."""

    template_name = "coin/coin.html"

    def get_num_txs(self, addrs):
        query = self.build_txs_query(
            list(zip(addrs, addrs)),
            return_="COUNT(transaction)"
        )
        return self.run_filters(query).single().value()

    def get_balance(self, addrs):
        query = self.build_nodes_query(addrs, "SUM(node.balance)")
        return self.run_query(query).single().value()

    def get_context_data(self, **kwargs):
        """Response data for coin template page."""
        
        context = super().get_context_data(**kwargs)
        self.kwargs["coin"] = self.kwargs["coin"].upper()
        session = self.request.user.get_coin(self.kwargs["coin"]).get_session(self.kwargs["session_id"])

        context["session"] = session.name

        # If a user defined group find the user's group in database.
        if "group_id" in self.kwargs:
            group = session.get_group(self.kwargs["group_id"])
            context["label"] = group.name
            context["addr"] = group.get_addrs()
        elif "addr" in self.kwargs:
            context["addr"] = [self.kwargs["addr"]]

            try:
                context["label"] = session.get_node(self.kwargs["addr"]).name
            except Http404:
                context["label"] = context["addr"]

            context["url"] = session.get_url() + "/addr/" + self.kwargs["addr"]
        elif self.request.GET.getlist("addr[]", None):
            context["addr"] = self.request.GET.getlist("addr[]")
            context["names"] = []

            for addr in context["addr"]:
                try:
                    context["names"] = session.get_node(addr).name
                except Http404:
                    context["names"].append(addr)

        # Query for sum of balances and total transactions for the addresses
        context["balance"] = self.get_balance(context["addr"])
        context["totalTxs"] = self.get_num_txs(context["addr"])

        context["filters"] = self.get_formatted_filter_values()
        context["dFilters"] = self.get_filter_defaults()

        return context


class TransactionsAPIView(QueryMixin, View):
    """View for processing requests getting 
    transaction data from neo4j."""

    @property
    def session(self):
        """User session with labels and groups."""

        return self.request.user.get_coin(self.kwargs["coin"]).get_session(self.kwargs["session_id"])

    def get_search_params(self) -> str:
        """Formats search parameters of transaction order, 
        property to sort, and page of transactions to return.

        Return
        ------
        str
            Formatted string of search parameters to add on to neo4j query.
        """

        order = self.request.GET.get("order", "DESC")
        sort = self.request.GET.get("sort", "blocktime")
        page = self.request.GET.get("page", 0)

        if page.isdigit():
            page = int(page)
        else:
            page = 0

        return (f"ORDER BY transaction.{sort} {order} "
                f"SKIP {page*TxsPerPage()} "
                f"LIMIT {TxsPerPage()}")

    def get_node_label(self, addr) -> str:
        """Get label of specified address 
        from user's session if it is labeled.

        Parameters
        ----------
        addr : str
            Address of node to check for in user session.

        Return
        ------
        str
            Label of node or address of node if not labeled.
        """

        try:
            node = self.session.get_node(addr)
            return node.name
        except Http404:
            return addr

    def get_context_data(self, **kwargs) -> dict:
        """Formatted transactions data to return as response."""

        context = []

        # Make sure coin label is uppercase for neo4j.
        self.kwargs["coin"] = self.kwargs["coin"].upper()

        # Get address in the form of a
        # list of tuples of senders and receivers.
        senders_or_receivers = list(zip(self.request.GET.getlist("addr[]", []),
                                        self.request.GET.getlist("addr[]", [])))
        senders_and_receivers = list(zip(self.request.GET.getlist("sender[]", []),
                                         self.request.GET.getlist("receiver[]", [])))

        # Build and execute query with list of addresses.
        addrs = senders_or_receivers + senders_and_receivers
        query = self.build_txs_query(addrs) + self.get_search_params()
        rows = self.run_filters(query)

        # Format transaction rows for response.
        for row in rows:
            tx = row["transaction"]
            sender = row["sender"]
            receiver = row["receiver"]

            context.append({
                "from": sender.id,
                "to": receiver.id,
                "value": float(tx["amount"]),
                "source": self.get_node_label(sender["addr"]),
                "sourceAddr": sender["addr"],
                "target": self.get_node_label(receiver["addr"]),
                "targetAddr": receiver["addr"],
                "type": tx["type_int"],
                "time": tx["blocktime"],
                "txid": tx["txid"],
                "img": self.session.coin.get_img(),
                "txidUrl": self.session.coin.get_url() + "/getTx/" + tx["txid"],
                "sourceUrl": self.session.get_url() + "/addr/" + sender["addr"],
                "targetUrl": self.session.get_url() + "/addr/" + receiver["addr"]
            })

        return context

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Return response as JSON."""

        return JsonResponse(self.get_context_data(), safe=False)


class GraphAPIView(QueryMixin, View):
    """View for processing requests getting 
    aggregate transaction data from neo4j."""

    # QueryFilter to specify transaction type from neo4j.
    txs_type = QueryFilter(
        property_name="type",
        value_name="type",
        variable_names=["NOT transaction"]
    )

    @property
    def last_id(self) -> int:
        """ID for offsetting IDs when user adds on to an existing graph."""

        last_id = self.request.GET.get("lastId")

        if not is_numeric(last_id):
            return 0
        return int(last_id)

    @property
    def session(self) -> Session:
        """User session with labels and groups."""

        return self.request.user.get_coin(self.kwargs["coin"]).get_session(self.kwargs["session_id"])

    def get_node_from_session(self, addr) -> dict:
        """Get node data of specified address 
        from user's session if it exists.

        Parameters
        ----------
        addr : str
            Address of node to check for in user session.

        Return
        ------
        dict
            Properties of node or address of node 
            if it does not exist in session.
        """

        try:
            node = self.session.get_node(addr)
            return {
                "name": node.name,
                "addr": node.addr,
                "url": node.get_url()
            }
        except Http404:
            return {
                "name": addr,
                "addr": addr,
                "url": self.session.get_url() + "/addr/" + addr
            }

    def get_node_data(self, node, cur_nodes, senders_or_receivers) -> dict:
        """Formats node data for graphing on frontend.

        Parameters
        ----------
        node : Node
            Neo4j node data.
        cur_nodes : list
            Current nodes already formatted to check 
            against so node is not added again to response.
        senders_or_receivers : list[(str, str)]
            List of addresses to check if this node already exists in graph.

        Return
        ------
        dict
            Formatted properties of node.
        """

        # Check if node exists in response data so far.
        existing_node = next(
            (cur_node
             for cur_node in cur_nodes if cur_node["id"] == node.id),
            None
        )

        # If node has already been added to
        # response data then return existing data.
        if existing_node:
            existing_node["url"] = None
            return existing_node

        # Get information of node from user's current session if it exists.
        node_info = self.get_node_from_session(node["addr"])

        # Node group for coloring on graph.
        node_group = "usdt"

        if (node["addr"], node["addr"]) in senders_or_receivers:
            node_group = "main"
        elif self.last_id > 0:
            node_group = "tempusdt"

        balance = float(node["balance"] or 0)
        formatted_balance = num_with_commas(balance, dec=3)

        node = {
            "id": node.id,
            "label": node_info["name"],
            "addr": node_info["addr"],
            "group": node_group,
            "url": node_info["url"],
            "value": balance,
            "img": self.session.coin.get_img(),
            "title": (f"Address: {node['addr']}<br> "
                      f"Balance: ${formatted_balance} ")
        }
        if node["label"] != node["addr"]:
            node["title"] = f"Name: {node['label']}<br> {node['title']}"

        if senders_or_receivers and (node["addr"], node["addr"]) not in senders_or_receivers:
            node["title"] += "<br> <b>Double Click to Load Transactions!</b>"

        return node

    def get_edge_data(self, edge, id, sender, receiver) -> dict:
        """Formats edge data for graphing on frontend.

        Parameters
        ----------
        edge : Relationship
            Neo4j relationship data.
        id : int
            ID for edge to set for graphing
        sender : str
            Address of sender node.
        receiver : str
            Address of receiver node.

        Return
        ------
        dict
            Formatted properties of edge.
        """

        edge = {
            "from": sender["id"],
            "to": receiver["id"],
            "id": id,
            "value": float(edge["totalAmount"] or 0),
            "source": sender["label"],
            "target": receiver["label"],
            "sourceAddr": sender["addr"],
            "targetAddr": receiver["addr"],
            "txsNum": int(edge["txsNum"] or 1.0),
            "avgTx": float(edge["avgTxAmt"] or edge["totalAmount"] or 0),
            "img": self.session.coin.get_img(),
            "color": {
                "color": "#26A17B" if self.last_id == 0 else "#AEB6BF"
            },
            "sourceUrl": self.session.get_url() + "/addr/" + sender["addr"],
            "targetUrl": self.session.get_url() + "/addr/" + receiver["addr"]
        }

        # Format numbers for edge description.
        formatted_txs_num = num_with_commas(edge["txsNum"], dec=3)
        formatted_total_amount = num_with_commas(edge["value"], dec=3)
        formatted_avg_amount = num_with_commas(edge["avgTx"], dec=3)

        edge["title"] = (f"# of Txs: {formatted_txs_num}<br> "
                         f"Total: ${formatted_total_amount}<br> "
                         f"Average Tx Amount: ${formatted_avg_amount}<br>")

        return edge

    def get_context_data(self, **kwargs) -> dict:
        """Formatted aggregate transactions data to return as response."""

        context = {}

        # Make sure coin label is uppercase for neo4j queries.
        self.kwargs["coin"] = self.kwargs["coin"].upper()

        # Get address in the form of a
        # list of tuples of senders and receivers.
        senders_or_receivers = list(zip(self.request.GET.getlist("addr[]", []),
                                        self.request.GET.getlist("addr[]", [])))
        senders_and_receivers = list(zip(self.request.GET.getlist("sender[]", []),
                                         self.request.GET.getlist("receiver[]", [])))

        # Build and execute query with list of addresses.
        addrs = senders_or_receivers + senders_and_receivers
        query = self.build_graph_query(addrs)
        rows = self.run_filters(query)

        context["nodes"] = []
        context["edges"] = []
        context["totalTxs"] = 0
        id = self.last_id

        # Format transaction rows for response
        for row in rows:
            id += 1
            sender = self.get_node_data(
                row["sender"],
                context["nodes"],
                senders_or_receivers
            )
            receiver = self.get_node_data(
                row["receiver"],
                context["nodes"],
                senders_or_receivers
            )

            edge = self.get_edge_data(
                row["aggTransaction"], id, sender, receiver)

            context['totalTxs'] += edge["txsNum"]

            if sender["url"]:
                context["nodes"].append(sender)
            if receiver["url"]:
                context["nodes"].append(receiver)
            context["edges"].append(edge)

        return context

    def get(self, request, *args, **kwargs):
        """Return response as JSON."""

        return JsonResponse(self.get_context_data(), safe=False)
