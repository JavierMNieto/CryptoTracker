from django import template

register = template.Library()

@register.filter(name='times')
def times(number):
    return range(1, number)

@register.filter(name='numCommas')
def numCommas(num):
    num = round(num, 2)
    return ("{:,}".format(num))