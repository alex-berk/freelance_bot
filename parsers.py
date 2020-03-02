import requests
from lxml import html
import json, csv
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


	def get(self):
		query_params = {'url': self.url}
		if self.headers: query_params['headers'] = self.headers
		logger.info(f"Sending request to {self.host}")
		try:
			r = requests.get(**query_params, timeout=60)
		except requests.exceptions.ReadTimeout:
			logger.error(f'Timeout Error from {self.host}')
			return {}
		return r.text

	def parse(self):
		tree = html.fromstring(self.get())
		tree.make_links_absolute(base_url=self.host)
		
		containers = tree.xpath(self.containers)

		parsed_objcts = []
		for objct in containers:
			extracted_fields = {}
			for field_name, extractor in self.extractors.items():
				if extractor:
					extracted_fields[field_name] = objct.xpath('.' + extractor)
					extracted_fields[field_name] = [obj.replace('\u202f', ' ').replace('\u200b', '').strip() for obj in extracted_fields[field_name]]
					if len(extracted_fields[field_name]) == 1:
						extracted_fields[field_name] = extracted_fields[field_name].pop()
					elif len(extracted_fields[field_name]) == 0:
						extracted_fields[field_name] = ''
				else:
					extracted_fields[field_name] = ''

			parsed_objcts.append(extracted_fields)

		logger.debug(f'Parsed {self.host}')
		return parsed_objcts

	@property
	def host(self):
		return '/'.join(self.url.split('/')[:3])

	@classmethod
	def parse_all(cls):
		with concurrent.futures.ThreadPoolExecutor() as executor:
			results = [executor.submit(inst.parse) for inst in cls.instances]
			return [f.result() for f in concurrent.futures.as_completed(results)]

	@staticmethod
	def get_gdoc_config(doc_id, page_id=0):
		url = f'https://docs.google.com/spreadsheets/d/{doc_id}/export'
		params = {'format': 'csv', 'gid': page_id}

		try:
			r = requests.get(url=url, params=params, timeout=120)
		except requests.exceptions.ReadTimeout:
			logger.error('Timeout Error')
			time.sleep(60)
			get_gdoc_confing(doc_id, page_id)

		reader = csv.reader(r.text.split('\r\n'), delimiter=',')
		table = [row for row in reader][1:]

		keys, values_col = [row[0] for row in table], [row[1:] for row in table]
		results = [{keys[i]: v[n] for i, v in enumerate(values_col)} for n in range(len(values_col[0]))]

		for index, result in enumerate(results):
			for field in result:
				try:
					results[index][field] = json.loads(results[index][field].replace("\'", "\""))
				except json.decoder.JSONDecodeError:
					pass
		
		typed_results = [(result.pop('parser_type'), result) for result in results]

		for parser_type, config in typed_results:
			if parser_type == 'Parser' or parser_type == '':
				Parser(**config)
			elif parser_type == 'JsonParser':
				JsonParser(**config)

		return typed_results


class JsonParser(Parser):
	def __init__(self, url, containers, headers=False, **extractors):
		super().__init__(url, containers, headers, **extractors)

	def parse(self):
		content = json.loads(self.get())
		for curr_selector in self.containers.split('//'):
			content = content[curr_selector]
		parsed_objcts = []
		for objct in content:
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

		logger.debug(f'Parsed {self.host}')
		return parsed_objcts

if __name__ == '__main__':

	'''Sample parser configs for testing
	'''
	
	# print(Parser.get_gdoc_config('1VGObmBB7RvgBtBUGW7lXVPvm6_m96BJpjFIH_qkZGBM'))

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

	guru_params = {
		'url': 'https://www.guru.com/api/search/job/',
		'headers': {'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbmFtZSI6IjM5NjY3MTUiLCJVVFkiOiJJIiwicm9sZSI6WyIyIiwiMTAxIl0sIlNJRCI6IjI5ODY0MzciLCJUSUQiOiIyMTIyOTA1IiwiSUFMIjoiRmFsc2UiLCJPSUQiOiIzOTY2NzE1IiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmd1cnUuY29tLyIsImF1ZCI6Imh0dHBzOi8vd3d3Lmd1cnUuY29tL2FwaSIsImV4cCI6MTU4MjU3MjMxMywibmJmIjoxNTgyNTY4NzEzfQ.JDsX8vi23FJaK_xDDQIeo_ptnsxqOK3EJ5KwngQbEaA'},

		'containers': 'Data//Results',

		'title': 'Title',
		'project_id': 'ProjectID',
		'tags': 'Skills',
		'price': 'BudgetAmountShortDescription'
	}

	freelansim = JsonParser(**flnsm_params)
	freelancehunt = Parser(**frlnchnt_params)
	guru = JsonParser(**guru_params)


	for index, instance in enumerate(Parser.instances):
		print(index, instance)

	for result in Parser.parse_all():
		for index, res in enumerate(result):
			print(index, res)
