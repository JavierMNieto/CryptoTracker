import sys

timeout = 3600.0 #seconds
satoshi = 100000000.0
minVal  = 100
neo4j   = {
	'user': 'neo4j',
	'pass': '2282002',
	'url': 'bolt://localhost:7687'
}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def logPrint(*args, **kwargs):
    print(*args, file=open("log.txt", "a"), **kwargs)

proxies = [
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow16-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow17-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow18-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow19-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow20-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow001-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow002-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow003-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow004-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow005-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow006-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow007-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow008-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow009-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow010-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow011-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow012-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow013-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow014-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow015-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow016-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow017-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow018-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow019-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow020-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow021-country-us:widow123@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_9579c5ab-zone-widow022-country-us:widow123@zproxy.lum-superproxy.io:22225'
	}
]