"""Utility functions and classes for coin app views


"""

from logging import ERROR
import re
from neo4j import GraphDatabase
from neo4j.work.result import Result
from .defaults import *

# ---------------- Helper Functions --------------


def num_with_commas(num: float, dec=0) -> str:
    """Formats number to string with commas and 
    rounded to specified decimal spaces.

    Parameters
    ----------
    num : float
        The number to format.
    dec : int, optional
        The number of decimal places to round number to.

    Returns
    -------
    str
        Formatted string of number.
    """

    if dec > 0:
        return ("{:,}".format(round(float(num), dec)))
    return ("{:,}".format(float(num)))


def is_numeric(val) -> bool:
    """Checks if value is able to be casted to a float.

    Parameters
    ----------
    val
        Value to check if numeric or not.

    Returns
    bool
        Whether value is numeric or not.
    """

    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


def is_valid_name(name: str) -> bool:
    """Checks if name for node or group is valid input
    between 2 and 16 characters with only 
    letters, numbers, spaces, hyphens, and underscores.

    Parameters
    ----------
    name : str
        Name of node or group to check validity of.

    Returns
    -------
    bool
        Whether name is valid or not.
    """

    return (len(name) < 16 and
            len(name) > 2 and
            re.match(r'^[A-Za-z0-9_ -]*$', name))


class QueryFilter():
    """Base class for all query filter types

    Query filters build strings for neo4j queries and for viewing 
    the filters on the frontend. Limits on the query filter may be 
    used to test when the filter should be added to a query and 
    how the filter should be formatted for the frontend.

    Parameters
    ----------
    property_name : str
        Property name stored in neo4j database.
    value_name : str
        Unique name of value passed through query parameters.
    variable_names : list
        Names of variables to apply filter on in neo4j query.
    operator : {'=', '<', '>', '<=', '>='}
        Operator as str to check against `property_name` with `value_name`.
    limit : int, optional
        Limit of value to check against property with `operator`.
    limit_label : str, optional
        Label for filter for when value is outside of `limit`.

    Methods
    -------
    to_str(join=" AND ")
        str of filter to add to query
    """

    def __init__(self, property_name=None, value_name=None,
                 variable_names=[], operator="=", limit=0,
                 limit_label=None):
        self.property_name = property_name
        self.value_name = value_name
        self.variable_names = variable_names
        self.operator = operator
        self.limit = limit
        self.limit_label = limit_label

    def to_str(self, join=" AND ") -> str:
        """Format all query filter attributes 
        into string for neo4j api to parse

        Parameters
        ----------
        join : {" AND ", " OR "}
            str to join all variable names together with

        Return
        ------
        str
            Formatted string for neo4j api.

        Examples
        --------

        """

        return join.join(
            (f"{variable_name}.{self.property_name} "
             f"{self.operator} {{{self.value_name}}}")
            for variable_name in self.variable_names
        )

    def is_within_limits(self, value=None) -> bool:
        """Check given value against query filter limit.

        Parameters
        ----------
        value
            Value to check against limit.

        Return
        ------
        bool
            Whether given value is within filter limits.
        """

        return self.limit == value

    def get_formatted(self, value=None) -> str:
        """Tests whether given value is within filter limits to either 
        return the given value or the limit label of filter.

        Parameters
        ----------
        value
            Value to check against limit.

        Return
        ------
        str
            Formatted value of this query filter.
        """

        if self.is_within_limits(value):
            return str(value)
        return self.limit_label


class MinNumberFilter(QueryFilter):
    """Query Filter subclass for filtering numeric properties 
    to be greater than or equal to the limit or a given value."""

    def __init__(self, property_name, value_name,
                 variable_names=[], limit=-1, limit_label="min"):
        super().__init__(property_name=property_name,
                         value_name=value_name,
                         operator=">=", limit=limit,
                         limit_label=limit_label,
                         variable_names=variable_names)

    def is_within_limits(self, value=None) -> bool:
        """Numeric types greater than or equal to the filter's limit."""

        return is_numeric(value) and float(value) > self.limit


class MaxNumberFilter(QueryFilter):
    """Query Filter subclass for filtering numeric properties 
    to be lesser than or equal to the limit or a given value."""

    def __init__(self, property_name, value_name,
                 variable_names=[], limit=1e14, limit_label="max"):
        super().__init__(property_name=property_name,
                         value_name=value_name,
                         variable_names=variable_names,
                         operator="<=", limit=limit,
                         limit_label=limit_label)

    def is_within_limits(self, value=None) -> bool:
        """Numeric types less than or equal to the filter's limit."""

        return is_numeric(value) and float(value) < self.limit


class QueryMixin:
    """Mixin for building Neo4j Queries for 
    Crypto Transactions with Django Views.

    Reads and formats user inputted query parameters to 
    compile data from neo4j database.

    Attributes
    ----------
    neo4j_driver : Neo4jDriver
        Driver for executing queries on Neo4j database.
    min_bal, max_bal : QueryFilter
        Filters for lower and upper bounds on node balance.
    min_tx, max_tx : QueryFilter
        Filters for lower and upper bounds on transaction amount.
    min_time, max_time : QueryFilter
        Filters for lower and upper bounds on transaction blocktime.
    min_total, max_total : QueryFilter
        Filters for lower and upper bounds on 
        total transaction amount sent between two nodes.
    min_txs_num, max_txs_num : QueryFilter
        Filters for lower and upper bounds on 
        number of transactions sent between two nodes. 
    min_avg, max_avg : QueryFilter
        'minAvg' Filters for lower and upper bounds on 
        average transaction amount sent between two nodes.
    SINGLE_TX_LIST : list
        List of filter value names that filter individual transactions.
    AGG_TX_LIST : list
        List of filter value names that filter aggregate transactions.
    NODE_MATCH
    TX_MATCH
    TX_ONLY_QUERY
    AGG_TX_QUERY
    AGG_TX_ONLY_QUERY
    GRAPH_QUERY

    Methods
    -------
    build_nodes_query(addrs=[], return_="node")
        Build query for getting node data.
    build_txs_query(addrs=[], return_"sender, receiver, transaction")
        Build query for getting transaction data.
    build_graph_query(addrs=[], return_"sender, receiver, aggTransaction")
        Build query for getting aggregate transactio data.
    """

    neo4j_driver = GraphDatabase.driver(
        Neo4j()['url'],
        auth=(Neo4j()['user'],
              Neo4j()['pass'])
    )

    # ------------- Query Filters -----------------
    min_bal = MinNumberFilter(
        "balance", "minBal",
        variable_names=["sender", "receiver"]
    )
    max_bal = MaxNumberFilter(
        "balance", "maxBal",
        variable_names=["sender", "receiver"]
    )
    min_tx = MinNumberFilter(
        "amount", "minTx",
        variable_names=["transaction"]
    )
    max_tx = MaxNumberFilter(
        "amount", "maxTx",
        variable_names=["transaction"]
    )
    min_time = MinNumberFilter(
        "blocktime", "minTime",
        limit=1230940800,
        limit_label="oldest",
        variable_names=["transaction"]
    )
    max_time = MaxNumberFilter(
        "blocktime", "maxTime",
        limit_label="latest",
        variable_names=["transaction"]
    )
    min_total = MinNumberFilter(
        "totalAmount", "minTotal",
        variable_names=["aggTransaction"]
    )
    max_total = MaxNumberFilter(
        "totalAmount", "maxTotal",
        variable_names=["aggTransaction"]
    )
    min_txs_num = MinNumberFilter(
        "txsNum", "minTxsNum",
        variable_names=["aggTransaction"]
    )
    max_txs_num = MaxNumberFilter(
        "txsNum", "maxTxsNum",
        variable_names=["aggTransaction"]
    )
    min_avg = MinNumberFilter(
        "avgTxAmt", "minAvg",
        variable_names=["aggTransaction"]
    )
    max_avg = MaxNumberFilter(
        "avgTxAmt", "maxAvg",
        variable_names=["aggTransaction"]
    )

    # Query Filter Groups
    SINGLE_TX_LIST = ["minBal", "maxBal", "minTx",
                      "maxTx", "minTime", "maxTime"]
    AGG_TX_LIST = ["minTotal", "maxTotal", "minTxsNum",
                   "maxTxsNum", "minAvg", "maxAvg"]

    # -------- Neo4j Queries -----------

    # Template to match nodes
    NODE_MATCH = """
        MATCH (node:{coin})
        {filters}
        RETURN {return_}
    """

    # Template to match relationships between two nodes 
    TX_MATCH = """
        MATCH (sender:{coin})-[transaction:{coin}TX]->(receiver:{coin})
        {filters}
    """

    # Template for formatting and returning 
    # single transactions from `TX_MATCH`
    TX_ONLY_QUERY = """
        RETURN {return_}
    """

    # Template for filtering aggregate transactions defined 
    # by sum of transaction amounts, number of transactions, 
    # and average transaction amount from `TX_MATCH`. Single transactions 
    # are collected and then transformed back into rows 
    # if `aggTransaction` satisfies the filters.
    AGG_TX_QUERY = """
        WITH sender, receiver, {{
            totalAmount: SUM(transaction.amount),
            txsNum: COUNT(transaction),
            avgTxAmt: SUM(transaction.amount)/COUNT(transaction)
        }} as aggTransaction,
        COLLECT(transaction) as transactions_list
        {filters}
        UNWIND transactions_list as transaction
        RETURN {return_}
    """
    
    # Template for returning and filtering the aggregate transaction 
    # between two nodes from `TX_MATCH` similarly to `AGG_TX_QUERY` 
    # but returns `aggTransaction` instead of the individual transactions.
    GRAPH_QUERY = """
        WITH sender, receiver, {{
            totalAmount: SUM(transaction.amount),
            txsNum: COUNT(transaction),
            avgTxAmt: SUM(transaction.amount)/COUNT(transaction)
        }} as aggTransaction 
        {filters}
        RETURN {return_}
    """

    def build_nodes_query(self, addrs=[], return_="node") -> str:
        """Constructs query for getting nodes from neo4j.
        
        Parameters
        ----------
        addrs : list
            Addresses of nodes to match on neo4j.
        return_ : str
            Return statement from neo4j using matched nodes.
        
        Return
        ------
        str
            Neo4j query for filtering and returning node data
        """

        # Build node matches from list of addrs if the list is not empty
        if addrs:
            filters = "WHERE " + self._get_node_matches(addrs)
        
        # Use `NODE_MATCH` template to format coin/node type, filters, 
        # and return statement into neo4j query
        return self.NODE_MATCH.format(
            coin=self.kwargs["coin"],
            filters=filters,
            return_=return_
        )

    def build_txs_query(self, addrs=[], return_="sender, receiver, transaction") -> str:
        """Constructs query for getting transactions and nodes from neo4j.
        
        Parameters
        ----------
        addrs : list[(str, str)]
            List of tuples in the form of sender and receiver 
            addresses to match on neo4j.
        return_ : str
            Return statement from neo4j using matched nodes 
            and transactions data.
        
        Return
        ------
        str
            Query for utilizing data of single transactions 
            between nodes from neo4j.
        """

        # Build `TX_MATCH` query with user filters on nodes and transactions
        match = self._get_tx_match(addrs)

        # Build list of filters from valid aggregate transactions 
        txs_filters = self.get_filters_within_limits(filter_group=self.AGG_TX_LIST)
        
        # If aggregate transaction filters are defined by user then 
        # add the filters to query with `AGG_TX_QUERY`
        if txs_filters:
            txs_filters = "WHERE " + txs_filters
            txs_filter_str = self.AGG_TX_QUERY.format(
                filters=txs_filters, 
                return_=return_
            )
        # If not defined then do not filter aggregate 
        # transactions with `TX_ONLY_QUERY`
        else:
            txs_filter_str = self.TX_ONLY_QUERY.format(return_=return_)

        return match + txs_filter_str

    def build_graph_query(self, addrs=[], return_="sender, receiver, aggTransaction") -> str:
        """Constructs query for gettings aggregate transactions and nodes from neo4j
        
        Parameters
        ----------
        addrs : list[(str, str)]
            List of tuples in the form of sender and receiver 
            addresses to match on neo4j.
        return_ : str
            Return statement from neo4j using matched nodes 
            and aggregate transactions data.
        
        Return
        ------
        str
            Query for utilizing data of aggregate transactions 
            between nodes from neo4j.
        """
        
        # Build `TX_MATCH` query with user filters on nodes and transactions
        match = self._get_tx_match(addrs)

        # Build list of filters from valid aggregate transaction 
        # filters from user
        txs_filters = self.get_filters_within_limits(filter_group=self.AGG_TX_LIST)
        
        if txs_filters:
            txs_filters = "WHERE " + txs_filters
        
        # Pass filters and return statement to `GRAPH_QUERY`
        txs_filter_str = self.GRAPH_QUERY.format(
            filters=txs_filters,
            return_=return_
        )

        return match + txs_filter_str

    def is_valid_addr(self, addr) -> bool:
        """Checks if specified address exists as node in neo4j database.
        
        Parameters
        ----------
        addr : str
            Address to check for on neo4j.
            
        Return
        ------
        bool
            Whether specified address exists or not.
        """
        
        return (re.match(r'^[A-Za-z0-9]{34}$', addr) and
                self.run_query(self.build_nodes_query([addr]), "node.addr").single())

    def run_filters(self, query: str) -> Result:
        """Executes neo4j query with valid user filters.
        
        Parameters
        ----------
        query : str
            Query to execute on neo4j database with filters.
        
        Return
        ------
        Result
            Neo4j response from query.
        """
        
        return self.run_query(query, **self.get_filter_values_within_limits())

    def run_query(self, query, **kwargs) -> Result:
        """Executes neo4j query.
        
        Parameters
        ----------
        query : str
            Query to execute on neo4j database.
        **kwargs
            Parameters to apply onto query through neo4j driver.
        
        Return
        ------
        Result
            Neo4j response from query.
        """
        return self.neo4j_driver.session().run(query, **kwargs)

    def get_filter_defaults(self) -> dict:
        """Gets names and limits of query filters.
        
        Return
        ------
        dict
            Dictionary of filter value names and their respective limits.
        """

        return {
            query_filter.value_name: query_filter.limit
            for query_filter in self._iter_filters()
        }

    def get_formatted_filter_values(self) -> dict:
        """Gets formatted values of user filter values by either using the 
        user's value or the filter's limit label if the value is not valid.
        
        Return
        ------
        dict
            Dictionary of filter value value name and their formatted values.
        """

        formatted_filters = {}
        for query_filter in self._iter_filters():
            key = query_filter.value_name
            value = self.request.GET.get(key)
            formatted_filters[key] = query_filter.get_formatted(value)
        
        return formatted_filters

    def get_filters_within_limits(self, filter_group=SINGLE_TX_LIST) -> str:
        """Gets valid filter strings within filter limits.

        Parameters
        ----------
        filter_group : list
            List of filter value names to join to string.
            
        Return
        ------
        str
            Joined string of filters to be used for neo4j query.
        """

        filters_within_limits = []
        for query_filter in self._iter_filters():
            key = query_filter.value_name
            value = self.request.GET.get(key)
            if query_filter.is_within_limits(value) and key in filter_group:
                filters_within_limits.append(query_filter.to_str())

        return " AND ".join(filters_within_limits)

    def get_filter_values_within_limits(self) -> dict:
        """Gets filter values from user that are within limits.
        
        Return
        ------
        dict
            Dictionary of filter values names and 
            filter values within limits of filter.
        """
        
        filter_values = {}
        for query_filter in self._iter_filters():
            key = query_filter.value_name
            value = self.request.GET.get(key)
            if query_filter.is_within_limits(value):
                filter_values[key] = float(value)

        return filter_values

    def _get_node_matches(self, addrs) -> str:
        """Formats addresses of nodes into string 
        for filters in neo4j query.
        
        Parameters
        ----------
        addrs : list
            Addresses to filter by.
        
        Return
        ------
        str
            Joined list of address filters on node.
        """
        
        return " OR ".join(
            f"node.addr='{addr}'"
            for addr in addrs
        )

    def _get_tx_node_matches(self, addrs: list) -> str:
        """Formats list of addresses of senders and 
        receivers into string for filters for `TX_MATCH`.
        
        Addresses can be inputted with a `!` sign to 
        specify not to filter by that address.
        
        Parameters
        ----------
        addrs : list[(str, str)]
            List of senders and receivers to construct string from.
        
        Return
        ------
        str
            Joined list of senders and receivers filter on nodes.
        """

        matches = []
        for (sender, receiver) in addrs:
            
            # If sender address is the same as receiver then 
            # this node can be either a sender or a receiver.
            if sender == receiver:
                join = "OR"
            else:
                join = "AND"

            # Format sender and receiver addresses into 
            # string joined by either `OR` or `AND`.
            match_str = "(sender.addr='{sender}' {join} receiver.addr='{receiver}')".format(
                sender=sender.replace("!", ""),
                join=join,
                receiver=receiver.replace("!", "")
            )

            # If this address is specified to not be included 
            # then add `NOT` to match.
            if "!" in sender:
                match_str = "NOT " + match_str

            matches.append(match_str)

        return " OR ".join(matches)

    def _get_tx_match(self, addrs: list) -> str:
        """Builds match string to add to query for transactions.

        Paramaters
        ----------
        addrs : list[(str, str)]
            List of tuples in the form of sender and receiver addresses.
        
        Return
        ------
        str
            Formatted `TX_MATCH` with filters on transaction and nodes.
        """

        filters = ""
        node_matches_str = self._get_tx_node_matches(addrs)
        tx_filters_str = self.get_filters_within_limits()

        if node_matches_str or tx_filters_str:
            filters += "WHERE "

            filters += node_matches_str

            if node_matches_str and tx_filters_str:
                filters += " AND "

            filters += tx_filters_str

        return self.TX_MATCH.format(coin=self.kwargs["coin"], filters=filters)
    
    def _iter_filters(self) -> QueryFilter:
        for attr_name in dir(QueryMixin):
            attr = getattr(QueryMixin, attr_name)
            if isinstance(attr, QueryFilter):
                yield attr
