import os
import time, datetime
import requests
import json
from bot_notifier import BotNotifier


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
		print(task['title'], task['price'], task['price_format'])
		if keyword_search(keywords, task['tags']) or keyword_search(keywords, task['title']):
			bot.send_job(task)
		processed_tasks.append(task['id'])

def get_tasks(retry=False):
	url = 'https://freelansim.ru/tasks?per_page=25&page=1'
	headers = {	'User-Agent':'Python Telegram bot',
				'Accept': 'application/json',
				'X-App-Version': '1'}
	try:
		r = requests.get(url, headers=headers)
		if retry: bot.send_message('Parser is up again')
	except ConnectionError:
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

if __name__ == '__main__':
	bot = BotNotifier(os.environ['BOT_TOKEN'], os.environ['CHAT_ID'])
	keywords = ['python', 'питон', 'пайтон', 'парс', 'спарсить', 'парсинг', 'телеграм', 'телеграмм', 'telegram', 'bot', 'бот', 'modx', 'seo', 'сео', 'продвижение', 'продвинуть', 'analytics', 'аналитикс', 'метрика', 'metrica', 'metrika', 'gtm', 'bi', 'query']

	processed_tasks = [task['id'] for task in get_tasks()]
	time.sleep(60)
	while True:
		print(f"\n[{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}] Sent request")
		print(processed_tasks)
		new_tasks = [task for task in get_tasks() if task['id'] not in processed_tasks]
		tasks_sender(new_tasks)
		time.sleep(60 * 5)
