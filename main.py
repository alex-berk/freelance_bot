import os, logging
import time, datetime
import requests
import json
import tgbot
from multiprocessing import Process

logger = logging.getLogger('__main__')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s', '%H:%M:%S')

if not os.path.exists('logs'): os.mkdir('logs')
a_date = datetime.date.today()
file_handler = logging.FileHandler(os.path.join('logs', str(a_date) + '.log'))
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('\n[%(asctime)s] %(message)s', '%H:%M:%S'))

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def keyword_search(keywords, body):
	try:
		body = body.lower().split()
	except AttributeError:
		body = [item.lower() for item in body]
		
	search = (word in body for word in keywords)
	for match in search:
		if match:
			return match
	return match

def tasks_sender(task_list): 
	for task in task_list[::-1]:
		print(f"{task['title']}, {task['price']}, {task['price_format']}")
		if keyword_search(keywords, task['tags']) or keyword_search(keywords, task['title']):
			logger.debug(f"Found task {task['id']}")
			bot.send_job(task)
		processed_tasks.append(task['id'])

def get_tasks(retry=False):
	url = 'https://freelansim.ru/tasks?per_page=25&page=1'
	headers = {	'User-Agent':'Telegram Freelance bot',
				'Accept': 'application/json',
				'X-App-Version': '1'}
	try:
		r = requests.get(url, headers=headers)
		if retry: bot.send_message('Parser is up again')
	except ConnectionError:
		logger.warning('Parser is down')
		bot.send_message('Parser is down. Going to try to reconnect in 1 minute.')
		time.sleep(60)
		get_tasks(retry=True)
	tasks = json.loads(r.text)['tasks']
	parsed_tasks = []
	for task in tasks:
		parsed_tasks.append({'title': task['title'], 'id': task['id'],
							'price': task['price']['value'], 'price_format': task['price']['type'],
							'tags': [tag['name'] for tag in task['tags']],
							'url': 'https://freelansim.ru' + task['href']})
	return parsed_tasks


def main():
	processed_tasks = [task['id'] for task in get_tasks()]
	logger.debug(f"New tasks {processed_tasks}")
	time.sleep(60)
	while True:

		if a_date != datetime.date.today():
			logger.removeHandler(file_handler)
			file_handler = logging.FileHandler(os.path.join('logs', str(datetime.date.today()) + '.log'))
			file_handler.setFormatter(formatter)
			logger.addHandler(file_handler)

		new_tasks = [task for task in get_tasks() if task['id'] not in processed_tasks]
		logger.debug(f"New tasks {[task['id'] for task in new_tasks]}")
		logger.info("Sent request for the new tasks")
		tasks_sender(new_tasks)
		time.sleep(60 * 5)

def subprocess():
	try:
		bot.listener.polling()
	except Exception as e:
		logger.error(e)
		subprocess()

bot = tgbot.BotNotifier(os.environ['BOT_TOKEN'], os.environ['CHAT_ID'])
keywords = ['python', 'питон', 'пайтон', 'парс', 'парсер', 'спарсить', 'парсинг', 'телеграм', 'телеграмм', 'telegram', 'bot', 'бот', 'modx', 'seo', 'сео', 'продвижение', 'продвинуть', 'analytics', 'аналитикс', 'метрика', 'metrica', 'metrika', 'gtm', 'bi', 'query']
processed_tasks = []

if __name__ == '__main__':
	logger.debug('Started')

	process_1 = Process(target=main)
	process_2 = Process(target=subprocess)
	process_1.start()
	process_2.start()
	process_1.join()
	process_2.join()
