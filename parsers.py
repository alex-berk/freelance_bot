import requests
from lxml import html
import json

def parse_freelansim(retry=False):
	url = 'https://freelansim.ru/tasks?per_page=25&page=1'
	headers = {	'User-Agent':'Telegram Freelance bot (@freelancenotify_bot)',
				'Accept': 'application/json',
				'X-App-Version': '1'}
	# logger.info("Sending request")
	try:
		r = requests.get(url, headers=headers)
		if retry: bot.send_message('Parser is up again')
	except TimeoutError as e:
		# logger.error(f'Got Timeout error: {e}')
		parse_tasks()
	except ConnectionError as e:
		# logger.error(f'Got Connection error: {e}')
		bot.send_message('Parser is down. Going to try to reconnect in 1 minute.')
		time.sleep(60)
		parse_tasks(retry=True)

	extractors = {
	# 'task_list': 'tasks',
	'title': 'title',
	'price': 'price/value',
	'price_format': 'price/type',
	'tags': 'tags//name',
	'url': 'href',}

	task_list = json.loads(r.text)['tasks']
	parsed_tasks = []
	for task in task_list:
		extracted_fields = {}
		for field_name, extractor in extractors.items():
			extractor, *subextractor = extractor.split('//')
			extractor = extractor.split('/')

			curr_field = task
			while extractor:
				curr_field = curr_field[extractor.pop(0)]

			if subextractor:
				extracted_fields[field_name] = [item[subextractor[0]] for item in curr_field]
			else:
				extracted_fields[field_name] = curr_field
		parsed_tasks.append(extracted_fields)

	return parsed_tasks

	# task_list = json.loads(r.text)['tasks']
	# tasks = [{'title': task['title'], 'id': task['id'],
	# 		'price': task['price']['value'], 'price_format': task['price']['type'],
	# 		'tags': [tag['name'] for tag in task['tags']],
	# 		'url': 'https://freelansim.ru' + task['href']}
	# 		for task in task_list]

	return tasks

def parse_freelancehunt():
	url = 'https://freelancehunt.com/projects'
	# headers = {'User-Agent':'Telegram Freelance bot (@freelancenotify_bot)'}
	r = requests.get(url)

	tree = html.fromstring(r.text)

	extractors = {
	'containers': '//table[contains(@class, "project-list")]/tbody/tr',
	'title': '/td/a[contains(@class, "visitable")]/text()',
	'url': '/td/a[contains(@class, "visitable")]/@href',
	'price': '/td//div[contains(@class, "price")]/text()',
	'currency': '/td//div[contains(@class, "price")]/span/text()'
	}

	containers = tree.xpath(extractors.pop('containers'))

	extracted_fields = []
	for field in containers:
		curr_field = {}
		for field_name, extractor in extractors.items():
			try:
				curr_field[field_name] = field.xpath('.' + extractor)[0]
				curr_field[field_name] = curr_field[field_name].replace('\u202f', ' ').strip()
			except IndexError:
				curr_field[field_name] = None
		extracted_fields.append(curr_field)

		# title = task.xpath('./a[@class="visitable "]/text()').pop()
		# url = task.xpath('./a[@class="visitable "]/@href').pop()
		# try:
		# 	price = task.xpath('.//div[contains(@class, "price")]/text()').pop(0)
		# 	currency = task.xpath('.//div[contains(@class, "price")]/span/text()').pop()
		# 	price = price.replace('\u202f', ' ').strip() + ' ' + currency

		# except:
		# 	price = ''
		
		# tasks.append( {'title': title, 'url': url, 'price': price} )
	return extracted_fields
