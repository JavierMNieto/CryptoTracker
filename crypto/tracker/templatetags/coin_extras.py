from django import template
from datetime import datetime

register = template.Library()

@register.filter(name='times')
def times(num):
    return range(1, num)

@register.filter(name='numCommas')
def numCommas(num):
    #num = round(num, 2)
    if not isNum(num):
        return num
    num = float(num)
    if num == int(num):
        num = int(num)
    return ("{:,}".format(num))

@register.filter(name='dict_key')
def dict_key(d, k):
    return d[k]

@register.filter(name="isNum")
def isNum(num):
    try:
        float("{}".format(num))
    except ValueError:
        return False
    else:
        return True

@register.filter(name="filterName")
def filterName(f):
    if "min" in f:
        f = f.replace("min", "")
        return "Min " + f
    f = f.replace("max", "")
    return "Max " + f

@register.filter(name="getDefault")
def getDefault(f):
    if f == 'minTime':
        return 'oldest'
    if f == 'maxTime':
        return 'latest'
    if 'min' in f:
        return 'min'
    return 'max'

@register.filter(name="formatTime")
def formatTime(t, f):
    return datetime.utcfromtimestamp(t).strftime(f)

@register.filter(name="contains")
def contains(string, word):
    return word.lower() in string.lower()

@register.filter(name="index")
def index(indexable, i):
    return indexable[i]