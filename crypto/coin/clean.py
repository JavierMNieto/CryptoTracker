import time
import re
from .defaults import *

def num_with_commas(num, dec=0):
    if dec > 0:
        return ("{:,}".format(round(float(num), dec)))
    return ("{:,}".format(float(num)))

"""
    Filters class which handles filters from user requests and formats 
    them for most efficient use for queries
    TODO: Find more efficient way to build filters from user requests
"""
class Filters:
    dFilters = DFilters()

    def __init__(self, filters=DFilters()):
        self.filters = self.dFilters.copy()

        for f, val in filters.items():
            if f in self.filters and (type(val) is int or type(val) is float):
                self.filters[f] = val

    def add_as_query_params(self, url):
        for f, val in self.filters.items():
            url += "&{}={}".format(f, val)
        
        return url.replace("?&", "?")

    def get_raw_filters(self, formatTime=True):
        filters = self.filters.copy()

        if not formatTime:
            return filters

        if filters["minTime"] < -1:
            filters["minTime"] = int(time.time() + filters["minTime"])

        if filters["maxTime"] < -1:
            filters["maxTime"] = int(time.time() + filters["maxTime"])    

        return filters 

    """
        Format filters by building dictionary of only valid filter types and filter values
    """
    def get_formatted_filters(self, formatTime=True):
        filters = {}

        for f, val in self.filters.items():
            if "min" in f:
                if val <= self.dFilters[f] and ("Time" not in f or val >= -1):
                    if "Time" in f:
                        filters[f] = 'oldest'
                    else: 
                        filters[f] = 'min'
                elif formatTime and "Time" in f and val < -1:
                    filters[f] = int(time.time() + val)
                else:
                    filters[f] = val
            elif f in self.dFilters and "max" in f:
                if val >= self.dFilters[f]:
                    if "Time" in f:
                        filters[f] = 'latest'
                    else: 
                        filters[f] = 'max'
                elif formatTime and "Time" in f and val < -1:
                    filters[f] = int(time.time() + val)
                else:
                    filters[f] = val
        
        return filters

    """
        Returns filters which do not have default values
    """
    def get_changed_filters(self):
        cFilters = {}

        for f, val in self.get_formatted_filters(formatTime=False).items():
            if type(val) is int or type(val) is float:
                cFilters[f] = val
        
        return cFilters

def in_arr(arr, val):
    for item in arr:
        if item == val:
            return True
    
    return False

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def is_valid_name(name):            
        return len(name) < 16 and len(name) > 2 and re.match(r'^[A-Za-z0-9_ -]*$', name) != None