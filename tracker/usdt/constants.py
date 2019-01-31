import sys

timeout = 300.0 #seconds
satoshi = 100000000
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
		'http':'socks5://x3234593:ZpSMx9ktPg@proxy-nl.privateinternetaccess.com:1080',
		'https':'socks5://x3234593:ZpSMx9ktPg@proxy-nl.privateinternetaccess.com:1080'
	},
	{

		'http':'http://lum-customer-hl_4856a1e8-zone-static-country-us:uc9xcu9fcfpi@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-static-country-us:uc9xcu9fcfpi@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone1-country-us:l2b77dfwx1jz@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone1-country-us:l2b77dfwx1jz@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone2-country-us:1zbuhqzyenlo@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone2-country-us:1zbuhqzyenlo@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone3-country-us:ubzmd1szj4i4@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone3-country-us:ubzmd1szj4i4@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone4-country-us:phcbsz4yzew0@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone4-country-us:phcbsz4yzew0@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone5-country-us:75m0632dewt7@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone5-country-us:75m0632dewt7@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone6-country-us:vdy91ua9vjd3@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone6-country-us:vdy91ua9vjd3@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone7-country-us:ymbfcmpyg5pl@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone7-country-us:ymbfcmpyg5pl@zproxy.lum-superproxy.io:22225'
	},
	{
		'http':'http://lum-customer-hl_4856a1e8-zone-zone8-country-us:fe7wys4boaqp@zproxy.lum-superproxy.io:22225',
		'https':'https://lum-customer-hl_4856a1e8-zone-zone8-country-us:fe7wys4boaqp@zproxy.lum-superproxy.io:22225'
	}
]