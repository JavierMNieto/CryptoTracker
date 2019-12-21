import time
import re
from .defaults import *

def numWithCommas(num):
    return ("{:,}".format(float(num)))

class Filters:
    dFilters = DFilters()

    def __init__(self, filters=DFilters()):
        self.filters = self.dFilters.copy()

        for f, val in filters.items():
            if f in self.filters and (type(val) is int or type(val) is float):
                self.filters[f] = val

    def addAsQueryParams(self, url):
        for f, val in self.filters.items():
            url += "&{}={}".format(f, val)
        
        return url.replace("?&", "?")

    def getRawFilters(self, formatTime=True):
        filters = self.filters.copy()

        if not formatTime:
            return filters

        if filters["minTime"] < -1:
            filters["minTime"] = int(time.time() + filters["minTime"])

        if filters["maxTime"] < -1:
            filters["maxTime"] = int(time.time() + filters["maxTime"])    

        return filters 

    ## CHANGE
    def getFormattedFilters(self, formatTime=True):
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

    def getChangedFilters(self):
        cFilters = {}

        for f, val in self.getFormattedFilters(formatTime=False).items():
            if type(val) is int or type(val) is float:
                cFilters[f] = val
        
        return cFilters


def inArr(arr, val):
    for item in arr:
        if item == val:
            return True
    
    return False

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def isValidName(name):            
        return len(name) < 16 and len(name) > 2 and re.match(r'^[A-Za-z0-9_ -]*$', name) != None