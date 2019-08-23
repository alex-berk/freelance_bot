import os
import time, datetime
import requests
import json
from bot_notifier import Bot_Notifier


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
		if task['id'] not in processed_tasks:
			print(task['title'], task['price'], task['price_format'])
			if keyword_search(keywords, task['tags']) or keyword_search(keywords, task['title']):
				bot.send_job(task)

def get_tasks(retry=False):
	url = 'https://freelansim.ru/tasks?per_page=25&page=1'
	headers = {	'User-Agent':'Python Telegram bot',
				'Accept': 'application/json',
				'X-App-Version': '1'
			}
	try:
		r = requests.get(url, headers=headers)
		if retry: bot.send_message('Parser is up again')
	except ConnectionError:
		bot.send_message('Parser is down. Going to try to reconnect in 1 minute.')
		time.sleep(60)
		get_tasks(retry=True)
	tasks = json.loads(r.text)['tasks']
	tasks_to_send = []
	for task in tasks:
		if task['id'] not in processed_tasks:
			tasks_to_send.append({'title': task['title'], 'id': task['id'],
								'price': task['price']['value'], 'price_format': task['price']['type'],
								'tags': [tag['name'] for tag in task['tags']],
								'url': 'https://freelansim.ru' + task['href']})
	return tasks_to_send

if __name__ == '__main__':
	bot = Bot_Notifier(os.environ['BOT_TOKEN'], os.environ['CHAT_ID'])
	processed_tasks = []
	keywords = ['python', 'питон', 'пайтон', 'парс', 'спарсить', 'парсинг', 'телеграм', 'телеграмм', 'telegram', 'bot', 'бот', 'modx', 'seo', 'сео', 'продвижение', 'продвинуть', 'analytics', 'аналитикс', 'метрика', 'metrica', 'metrika', 'gtm', 'bi', 'query']

	processed_tasks = [task['id'] for task in get_tasks()]
	while True:
		tasks = get_tasks()
		print(f"\n[{datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}] Sent request")
		new_tasks = [task for task in tasks if task not in processed_tasks]
		tasks_sender(new_tasks)
		processed_tasks.extend([task['id'] for task in new_tasks])
		time.sleep(60 * 5)
