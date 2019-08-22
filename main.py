import os
import time, datetime
import requests
import json


def bot_send_msg(token, chat, text):
	r = requests.get(f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat}&text={text}')
	success = json.loads(r.text)['ok']
	if not success:
		print('Message not been sent!, Got response:\n', r.text, text)
	return success

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
			print(task['title'], task['price'])
		if task['id'] not in processed_tasks and keyword_search(keywords, task['title']) or keyword_search(keywords, task['tags']):
			title = task['title']
			price = task['price']
			url = task['url']
			tags = ', '.join(task['tags'])
			msg = f'[{title}]({url})\n*{price}*\n_{tags}_'
			bot_send_msg(bot_token, chat_id, msg)

def get_tasks(retry=False):
	url = 'https://freelansim.ru/tasks?per_page=25&page=1'
	headers = {	'User-Agent':'Python Telegram bot',
				'Accept': 'application/json',
				'X-App-Version': '1'
			}
	try:
		r = requests.get(url, headers=headers)
		if retry: bot_send_msg(bot_token, chat_id, 'Parser is up again')
	except ConnectionError:
		bot_send_msg(bot_token, chat_id, 'Parser is down. Going to try to reconnect in 1 minute.')
		time.sleep(60)
		get_tasks(retry=True)
	tasks = json.loads(r.text)['tasks']
	tasks_to_send = []
	for task in tasks:
		if task['id'] not in processed_tasks:
			tasks_to_send.append({'title': task['title'], 'id': task['id'],
								'price': '{} / {}'.format(task['price']['value'], task['price']['type']),
								'tags': [tag['name'] for tag in task['tags']],
								'url': 'https://freelansim.ru' + task['href']})
	return tasks_to_send

if __name__ == '__main__':
	bot_token = os.environ['BOT_TOKEN']
	chat_id = os.environ['CHAT_ID']
	processed_tasks = []
	keywords = ['python', 'питон', 'пайтон', 'парс', 'спарсить', 'парсинг', 'телеграм', 'телеграмм', 'telegram', 'bot', 'бот', 'modx', 'seo', 'сео', 'продвижение', 'продвинуть']

	processed_tasks = [task['id'] for task in get_tasks()]
	while True:
		tasks = get_tasks()
		print('\n[{}] Sent request'.format(datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')))
		new_tasks = [task for task in tasks if task not in processed_tasks]
		tasks_sender(new_tasks)
		processed_tasks.extend([task['id'] for task in new_tasks])
		time.sleep(60 * 5)
