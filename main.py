import os, logging
from multiprocessing import Process
import time, datetime
import requests
import json
import tgbot
import db_handler

logger = logging.getLogger('__main__')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s', '%H:%M:%S')

if not os.path.exists('logs'): os.mkdir('logs')
a_date = datetime.date.today()
file_handler = logging.FileHandler(os.path.join('logs', str(a_date) + '.log'))
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def string_cleaner(dirty_srtring):
	word_list, curr_word = [], ''
	for s in dirty_srtring:
		if s.isalpha():
			curr_word += s.lower()
		else:
			if curr_word: word_list.append(curr_word)
			curr_word = ''
	if curr_word: word_list.append(curr_word)
	return word_list

def tasks_sender(task_list):
	for task in task_list[::-1]:
		search_body = set(string_cleaner(task['title']) + task['tags'])
		relevant_users = db_handler.get_relevant_users_ids(search_body)
		if relevant_users: logger.debug(f"Found task {task['id'], task['tags']} for the users {relevant_users}")
		for user_id in relevant_users:
			bot.send_job(task, user_id)

def parse_tasks(retry=False):
	url = 'https://freelansim.ru/tasks?per_page=25&page=1'
	headers = {	'User-Agent':'Telegram Freelance bot (@freelancenotify_bot)',
				'Accept': 'application/json',
				'X-App-Version': '1'}
	logger.info("Sending request")
	try:
		r = requests.get(url, headers=headers)
		if retry: bot.send_message('Parser is up again')
	except ConnectionError:
		logger.warning('Parser is down')
		bot.send_message('Parser is down. Going to try to reconnect in 1 minute.')
		time.sleep(60)
		parse_tasks(retry=True)
	tasks = json.loads(r.text)['tasks']
	parsed_tasks = []
	for task in tasks:
		parsed_tasks.append({'title': task['title'], 'id': task['id'],
							'price': task['price']['value'], 'price_format': task['price']['type'],
							'tags': [tag['name'] for tag in task['tags']],
							'url': 'https://freelansim.ru' + task['href']})
	return parsed_tasks

def check_date_on_logger():
	global file_handler, a_date
	if a_date != datetime.date.today():
		a_date = datetime.date.today()
		logger.removeHandler(file_handler)
		formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s', '%H:%M:%S')
		file_handler = logging.FileHandler(os.path.join('logs', str(a_date) + '.log'))
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)


def main():
	while True:
		check_date_on_logger()
		new_tasks = [task for task in parse_tasks() if task['id'] not in db_handler.get_tasks_ids() and not db_handler.check_task_id(task['id'])]
		logger.debug(f"New tasks {[task['id'] for task in new_tasks]}")
		for task in new_tasks:
			print(f"{task['title']}, {task['price']}, {task['price_format']}")
			logger.debug(f"Sending task {task['id']} to db")
			db_handler.add_task(task)
		tasks_sender(new_tasks)
		time.sleep(60 * 5)

def subprocess():
	bot.polling()


bot = tgbot.BotNotifier(os.environ['BOT_TOKEN'], os.environ['CHAT_ID'])

if __name__ == '__main__':
	os.system('cls' if os.name=='nt' else 'clear')
	logger.debug('Started')

	process_1 = Process(target=main)
	process_2 = Process(target=subprocess)
	process_1.start()
	process_2.start()
	process_1.join()
	process_2.join()
