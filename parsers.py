import requests
from lxml import html
import json
import logging
import time
import concurrent.futures

logger = logging.getLogger('__main__')

class Parser:
	instances = []

	def __init__(self, url, containers, headers=False, **extractors):
		self.url = url
		self.containers = containers
		self.headers = headers
		self.extractors = extractors

		self.__class__.instances.append(self)

	def __repr__(self):
		return f"{self.__class__.__name__}({', '.join([key + '=' + repr(value) for key, value in self.__dict__.items()])})"


	def parse(self):
		query_params = {'url': self.url}
		if self.headers: query_params['headers'] = self.headers
		try:
			logger.info(f"Sending request to {self.host}")
			r = requests.get(**query_params)
			logger.info(f"Sent request to {self.host}")
		except (requests.exceptions.ConnectionError) as e:
			logger.error(e)
			return {}

		tree = html.fromstring(r.text)
		containers = tree.xpath(self.containers)

		parsed_objcts = []
		logger.info('Got parsed objcts')
		for objct in containers:
			extracted_fields = {}
			for field_name, extractor in self.extractors.items():
				if extractor:
					try:
						extracted_fields[field_name] = objct.xpath('.' + extractor)[0]
						extracted_fields[field_name] = extracted_fields[field_name].replace('\u202f', ' ').replace('\u200b', '').strip()
					except IndexError:
						extracted_fields[field_name] = ''
				else:
					extracted_fields[field_name] = ''

			if extracted_fields.get('link', 'http')[:4] !='http':
				extracted_fields['link'] = self.host + extracted_fields['link']

			parsed_objcts.append(extracted_fields)

		logger.info('Returning parsed_objcts')
		return parsed_objcts

	@property
	def host(self):
		return '/'.join(self.url.split('/')[:3])

	@classmethod
	def parse_all(cls):
		with concurrent.futures.ThreadPoolExecutor() as executor:
			results = [executor.submit(inst.parse) for inst in cls.instances]
			return [f.result() for f in concurrent.futures.as_completed(results)]


class JsonParser(Parser):
	def __init__(self, url, containers, headers=False, **extractors):
		super().__init__(url, containers, headers, **extractors)

	def parse(self):
		query_params = {'url': self.url}
		if self.headers: query_params['headers'] = self.headers
		try:
			logger.info(f"Sending request to {self.host}")
			r = requests.get(**query_params)
		except (requests.exceptions.TimeoutError) as e:
			logger.error(e)
			return {}

		containers = json.loads(r.text)[self.containers]
		parsed_objcts = []
		for objct in containers:
			extracted_fields = {}
			for field_name, extractor in self.extractors.items():
				extractor, *subextractor = extractor.split('//')
				extractor = extractor.split('/')

				curr_field = objct
				try:
					while extractor:
						curr_field = curr_field[extractor.pop(0)]
					if subextractor:
						extracted_fields[field_name] = [item[subextractor[0]] for item in curr_field]
					else:
						extracted_fields[field_name] = curr_field
				except KeyError:
					extracted_fields[field_name] = ''

			if extracted_fields.get('link', 'http')[:4] !='http':
				extracted_fields['link'] = self.host + extracted_fields['link']

			parsed_objcts.append(extracted_fields)

		return parsed_objcts

if __name__ == '__main__':

	flnsm_params = {
		'url': 'https://freelansim.ru/tasks',
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

	freelansim = JsonParser(**flnsm_params)
	freelancehunt = Parser(**frlnchnt_params)

	for result in Parser.parse_all():
		for index, res in enumerate(result):
			print(index, res)
