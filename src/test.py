import requests

usdtUrl = "https://api.omniwallet.org/v1/address/addr/details/"
proxy = {
		'http':'http://lum-customer-hl_9579c5ab-zone-widow16-country-us:widow123@zproxy.lum-superproxy.io:22225'
	}


resp = (requests.post(usdtUrl, data = {'addr': "1EXoDusjGwvnjZUyKkxZ4UHEf77z6A5S4P", 'page': 1}, proxies=proxy)).json()

print(resp)