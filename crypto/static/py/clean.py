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

    ## CHANGE
    def getFormattedFilters(self):
        filters = {}

        for f, val in self.filters.items():
            if "min" in f:
                if val <= self.dFilters[f]:
                    if "time" in f.lower():
                        filters[f] = 'oldest'
                    else: 
                        filters[f] = 'min'
                else:
                    filters[f] = val
            elif f in self.dFilters and "max" in f:
                if val >= self.dFilters[f]:
                    if "time" in f.lower():
                        filters[f] = 'latest'
                    else: 
                        filters[f] = 'max'
                else:
                    filters[f] = val
        
        return filters

    def getChangedFilters(self):
        cFilters = {}

        for f, val in self.getFormattedFilters().items():
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