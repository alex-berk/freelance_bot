import requests
from lxml import html
import json

def parse_freelansim(url, containers, headers=False, **extractors):
	query_params = {'url': url}
	if headers: query_params['headers'] = headers
	try:
		r = requests.get(**query_params)
	except (TimeoutError, ConnectionError) as e:
		return {'error': e}

	containers = json.loads(r.text)[containers]
	parsed_objcts = []
	for objct in containers:
		extracted_fields = {}
		for field_name, extractor in extractors.items():
			extractor, *subextractor = extractor.split('//')
			extractor = extractor.split('/')

			curr_field = objct
			try:
				while extractor:
					curr_field = curr_field[extractor.pop(0)]
				if subextractor:
					extracted_fields[field_name] = [item[subextractor[0]].replace('\u202f', ' ').replace('\u200b', '').strip() for item in curr_field]
				else:
					extracted_fields[field_name] = curr_field.replace('\u202f', ' ').replace('\u200b', '').strip()
			except KeyError:
				extracted_fields[field_name] = None
		parsed_objcts.append(extracted_fields)

	return parsed_objcts


def parse_freelancehunt(url, containers, headers=False, **extractors):
	query_params = {'url': url}
	if headers: query_params['headers'] = headers
	try:
		r = requests.get(**query_params)
	except (TimeoutError, ConnectionError) as e:
		return {'error': e}

	tree = html.fromstring(r.text)
	containers = tree.xpath(containers)

	parsed_objcts = []
	for objct in containers:
		extracted_fields = {}
		for field_name, extractor in extractors.items():
			if extractor:
				try:
					extracted_fields[field_name] = objct.xpath('.' + extractor)[0]
					extracted_fields[field_name] = extracted_fields[field_name].replace('\u202f', ' ').replace('\u200b', '').strip()
				except IndexError:
					extracted_fields[field_name] = None
			else:
				extracted_fields[field_name] = None
		parsed_objcts.append(extracted_fields)

	return parsed_objcts


flnsm_params = {
	'url': 'https://freelansim.ru/tasks?per_page=25&page=1',
	'headers': {'User-Agent':'Telegram Freelance bot (@freelancenotify_bot)', 'Accept': 'application/json', 'X-App-Version': '1'},

	'containers': 'tasks',

	'title': 'title',
	'price': 'price/value',
	'price_format': 'price/type',
	'tags': 'tags//name',
	'link': 'href',
	'test': ''
}

frlnchnt_params = {
	'url': 'https://freelancehunt.com/projects',

	'containers': '//table[contains(@class, "project-list")]/tbody/tr',

	'title': '/td/a[contains(@class, "visitable")]/text()',
	'link': '/td/a[contains(@class, "visitable")]/@href',
	'price': '/td//div[contains(@class, "price")]/text()',
	'currency': '/td//div[contains(@class, "price")]/span/text()',
	'tags': ''
}

for index, task in enumerate(parse_freelansim(**flnsm_params)):
	print(index, task)

for index, task in enumerate(parse_freelancehunt(**frlnchnt_params)):
	print(index, task)
