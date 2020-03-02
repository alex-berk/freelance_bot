 #coding=utf-8

import os, logging
import argparse
import concurrent.futures
import time, datetime
import requests
import json, csv
from utils import log_parser, db_handler, parse_string
from bot import bot
from parsers import Parser, JsonParser
from dashboard import app


argparser = argparse.ArgumentParser(description='You can specify whether you want to run only parser or bot part of the script')
argparser.add_argument('part', nargs="*", default=['all'], help='Name of the part you want to run (bot, parser or dashboard)')
argparser.add_argument('-port', default=5000, help='Port to run dashboard on')
argparser.add_argument('-host', default='127.0.0.1', help='Host to run dashboard on')
args = argparser.parse_args()

logger = logging.getLogger('__main__')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))

logger.addHandler(stream_handler)

a_date = datetime.date.today()

def set_file_logger():
	logger.handlers = [handler for handler in logger.handlers if handler.name != 'file_handler']

	if not os.path.exists('logs'): os.mkdir('logs')
	file_handler = logging.FileHandler(os.path.join('logs', str(a_date) + '.log'))
	formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s', '%H-%M-%S')

	file_handler.setFormatter(formatter)
	file_handler.set_name('file_handler')
	logger.addHandler(file_handler)
set_file_logger()

def tasks_sender(task_list):
	for task in task_list[::-1]:
		if task['tags']:
			search_body = set(parse_string(task['title']) + task['tags'])
		else:
			search_body = parse_string(task['title'])
		relevant_users = db_handler.get_relevant_users_ids(search_body)
		if relevant_users: logger.debug(f"Found task {task['link'], task['tags']} for the users {relevant_users}")
		for user_id in relevant_users:
			logger.debug(f"Sending task {task['link']}")
			tags = ', '.join(task['tags']) if task['tags'] else ''
			price_usd = '<i>(~ ' + '{:,}'.format(round(task['price_usd'])).replace(',', ' ') + '$)</i>' if task['price_usd'] else ''
			price = ' '.join([str(task['price']), task['currency'], price_usd])
			if task['price_format'] == 'per_hour': price += ' <i>за час</i>' 
			text = f"<b>{task['title']}</b>\n{price}\n<code>{tags}</code>"
			resp = bot.send_message(text, link=task['link'], chat_id=user_id, disable_preview=True)
			if resp in [400, 403]:
				logger.warning(f"Bot was kicked from the chat {user_id}. Deleting chat from db.")
				db_handler.delete_user(user_id)

def format_task(task):
	if task.get('tags_s'):
		task['tags'] = [i.lower().strip() for i in task['tags_s'].split(',')]

	if type(task['tags']) is not list:
		task['tags'] = [task['tags']]

	if task['price'] and task['price'][-1] == '₽':
		task['price'], task['currency'] = task['price'][:-2], task['price'][-1]

	if task['price'].strip() == '': task['price'] = 'Договорная'

	if task['currency'] == '₽':
		task['price_usd'] = int(task['price'].replace(' ', '')) * 0.015
	elif task['currency'] == '₴':
		task['price_usd'] = int(task['price'].replace(' ', '')) * 0.04
	else:
		task['price_usd'] = ''

	return task

def parser():
	global a_date
	parsed_tasks_links = []

	Parser.get_gdoc_config('1VGObmBB7RvgBtBUGW7lXVPvm6_m96BJpjFIH_qkZGBM')

	while True:
		if a_date != datetime.date.today():
			a_date = datetime.date.today()
			set_file_logger()
		
		parsed_tasks = []
		for batch in Parser.parse_all():
			parsed_tasks.extend(batch)
		new_tasks = [task for task in parsed_tasks if task['link'] not in parsed_tasks_links and not db_handler.check_task_link(task['link'])]
		logger.debug(f"New tasks {[task['link'] for task in new_tasks]}")

		for task in new_tasks:
			task = format_task(task)
			print(f"{', '.join([task['title'], task['price'], task['currency'], task['price_format']])}")
			logger.debug(f"Sending task {task['link']} to db")
			db_handler.add_task(task)
		tasks_sender(new_tasks)
		parsed_tasks_links = [task['link'] for task in parsed_tasks]
		time.sleep(60 * 5)


def bot_listener():
	bot.polling()

if __name__ == '__main__':
	logger.debug('Started')
	
	inline_argument = args.part.pop()
	if inline_argument == 'parser':
		parser()
	elif inline_argument == 'bot':
		bot_listener()
	elif inline_argument == 'dashboard':
		host, port = args.host, args.port
		app.run(debug=True, host=host, port=port)
	elif inline_argument == 'all':
		with concurrent.futures.ThreadPoolExecutor() as executor:
			threads = [executor.submit(parser), executor.submit(bot_listener), executor.submit(app.run)]

			for f in concurrent.futures.as_completed(threads):
				f.result()
	else:
		raise KeyError('Invalid argument')
