 #coding=utf-8

import os, logging
import argparse
import concurrent.futures
import time, datetime
import requests
import json, csv
import tgbot
import db_handler
from parsers import Parser, JsonParser
import log_parser

logger = logging.getLogger('__main__')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))

logger.addHandler(stream_handler)


argparser = argparse.ArgumentParser(description='You can specify whether you want to run only parser or bot part of the script')
argparser.add_argument('part', nargs="*", default=['both'], help='Name of the part you want to run (bot or parser)')
args = argparser.parse_args()


bot = tgbot.BotNotifier(os.environ['BOT_TOKEN'], int(os.environ['CHAT_ID']))


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

def parse_string(string, sep=None):
	word_list = [i.lower() for i in string.split(sep)]
	cleaned_list = []
	for word in word_list:
		cleaned_word = ''
		for symb in word:
			if symb.isalpha() or symb.isdigit() or symb == ' ':
				cleaned_word += symb
			else:
				cleaned_word += ' '
		cleaned_word = cleaned_word.strip()
		if cleaned_word and cleaned_word not in cleaned_list: cleaned_list.append(cleaned_word)
	return cleaned_list

def tasks_sender(task_list):
	for task in task_list[::-1]:
		if task['tags']:
			search_body = set(parse_string(task['title']) + task['tags'])
		else:
			search_body = set(parse_string(task['title']))
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


def setup_keys(chat_id):
	current_keys = db_handler.get_user_skeys(chat_id)
	if current_keys and bot.context.get(chat_id) != 'setup_keys_replace':
		bot.context[chat_id] = {'name': 'setup_keys'}
		bot.send_message(f'Ваши текущие ключевые слова для поиска:\n<b>{", ".join(current_keys)}</b>\n\nВы хотите добавить новые ключи к существующим, удилить некоторые из них или заменить весь список?', chat_id, keyboard=(['Добавить', 'Заменить', 'Удалить', '❌ Отмена'], 3))
	else:
		bot.context[chat_id] = {'name': 'setup_keys_init'}
		setup_text = 'Сейчас можно будет задать ключевые слова для поиска.\nКаждый раз, когда бот будет находить их в задаче, вам придет оповещение.\nКлючи разделяются запятой.\nДопускается использование только букв, цифр и пробелов.\nПоиск осуществляется по тегам и отдельным словам из заголовков, так что лучше задавать однословные ключи.\n\n<code>Пример:</code>\n<code>node js, java script, js, фронтенд</code>'
		bot.send_message(setup_text, chat_id, keyboard=['❌ Отмена'])

def confirm_keys_setup(chat_id, s_keys):
	confirm_text = 'Все готово. Ваши ключевые слова для поиска:\n<b>' + ", ".join(s_keys) + '</b>\n\nНачинаю отслеживать задачи'
	bot.send_message(confirm_text, chat_id)
	bot.send_sticker('CAADAgADBwIAArD72weq7luNKMN99BYE', chat_id)
	bot.context[chat_id] = None

@bot.commands_handler
def handle_commands(message):
	logger.debug(f'Got message from @{message["from"]["username"]}, id{message["from"]["id"]}{" in chat " + str(message["chat"]["id"]) if message["chat"]["type"] == "group" else ""}, {message["chat"]["title"] if message["chat"]["type"] == "group" else message["chat"]["type"]}, with text "{message["text"]}"')
	if bot.verify_command(message["text"], 'status'):
		status_text = 'Up and running!'
		if message["chat"]["id"] == bot.admin_chat_id:
			c_log = log_parser.get_current_log()
			ltg = log_parser.search_last_telegram_response(c_log)
			lp = log_parser.get_last_parsing(c_log)
			lp_s = ''.join([f'{k}: {v}\n' for (k, v) in lp])
			nt = log_parser.get_new_tasks_q(c_log)
			nt_s = '\n'.join([f'{k}: {v}' for (k, v) in nt.items()])
			status_text = f"\n<b>Last Telegram Response:</b>{ltg}\n\n<b>Last Parsing:</b>\n{lp_s}\n<b>Found Tasks Today:</b>\n{nt_s}\n"
		if bot.context.get(message["chat"]["id"], {'name': None})['name']:
			status_text += '\n<b>Current setup step:</b> ' + bot.context[message["chat"]["id"]]['name']
		bot.send_message(status_text, message["chat"]["id"], disable_preview=True)
	
	elif bot.verify_command(message["text"], 'start'):
		if db_handler.get_user_skeys(message["chat"]["id"]):
			bot.send_message('У вас уже настроены ключевые слова для поиска.\nЗаново их задать можно коммандой /keywords', message["chat"]["id"])
		else:
			setup_keys(message["chat"]["id"])
	
	elif bot.verify_command(message["text"], 'keywords'):
		bot.context.pop(message["chat"]["id"], None)
		setup_keys(message["chat"]["id"])

	elif bot.verify_command(message["text"], 'stop'):
		bot.context[message["chat"]["id"]] = {'name': 'stop_tacking'}
		bot.send_message('Вы точно хотите остановить отслеживание?', message["chat"]["id"], keyboard=['Да', 'Нет'])

	elif bot.verify_command(message["text"], 'cancel'):
		bot.context.pop(message["chat"]["id"], None)
		bot.send_message('Действие отменено', message["chat"]["id"])
	
@bot.message_handler
def handle_text(message):
	if message["text"].lower() in ['нет', '❌ отмена']:
		if bot.context.get(message["chat"]["id"], None):
			bot.context.pop(message["chat"]["id"])
			bot.send_message('Действие отменено', message["chat"]["id"])
		else:
			bot.send_message('Нечего отменить', message["chat"]["id"])
	
	elif bot.verify_context_message(message, 'setup_keys', 'добавить'):
		bot.context[message["chat"]["id"]] = {'name': 'setup_keys_add'}
		bot.send_message(f'Напишите через запятую слова, которые нужно добавить к вашему списку', message["chat"]["id"], keyboard=['❌ Отмена'])

	elif bot.verify_context_message(message, 'setup_keys', 'заменить'):
		bot.context[message["chat"]["id"]] = {'name': 'setup_keys_replace'}
		bot.send_message(f'Напишите слова, которыми нужно заменить существующие', message["chat"]["id"], keyboard=['❌ Отмена'])

	elif bot.verify_context_message(message, 'setup_keys', 'удалить'):
		bot.context[message["chat"]["id"]] = {'name': 'setup_keys_delete'}
		bot.context[message["chat"]["id"]]['working_keys'] = db_handler.get_user_skeys(message["chat"]["id"])
		bot.send_message(f'Напишите слова, которые нужно удалить через запятую или выберете их внизу, на выпадающей клавиатуре', message["chat"]["id"], keyboard=['✅ Готово', '❌ Отмена'] + bot.context[message["chat"]["id"]]['working_keys'])

	elif bot.verify_context_message(message, 'setup_keys_add'):
		s_keys_old = db_handler.get_user_skeys(message["chat"]["id"])
		s_keys_new = [key for key in  parse_string(message["text"], sep=',') if key not in s_keys_old]
		s_keys = s_keys_old + s_keys_new
		db_handler.update_user_keys(message["chat"]["id"], s_keys)
		confirm_keys_setup(message["chat"]["id"], s_keys)
	
	elif bot.verify_context_message(message, 'setup_keys_init') or bot.verify_context_message(message, 'setup_keys_replace'):
		s_keys = parse_string(message["text"], sep=',')
		try:
			db_handler.add_user(message["chat"]["id"], s_keys)
		except db_handler.sqlite3.IntegrityError:
			db_handler.update_user_keys(message["chat"]["id"], s_keys)
		confirm_keys_setup(message["chat"]["id"], s_keys)
	
	elif bot.verify_context_message(message, 'setup_keys_delete'):
		msg_words = parse_string(message["text"].lower(), ',')
		if msg_words == ['готово']:
			db_handler.update_user_keys(message["chat"]["id"], bot.context[message["chat"]["id"]]['working_keys'])
			confirm_keys_setup(message["chat"]["id"], bot.context[message["chat"]["id"]]['working_keys'])
			bot.context.pop(message["chat"]["id"], None)
		else:
			for word in msg_words:
				try:
					bot.context[message["chat"]["id"]]['working_keys'].remove(word)
					bot.send_message(f'Удалил <b>{word}</b>\nКогда закончите, нажмите "Готово" для того чтобы применить изменения.' , message["chat"]["id"], keyboard=['✅ Готово', '❌ Отмена'] + bot.context[message["chat"]["id"]]['working_keys'])
				except ValueError:
					bot.send_message(f'Не нашёл слова <b>{word}</b>' , message["chat"]["id"], keyboard=['✅ Готово', '❌ Отмена'] + bot.context[message["chat"]["id"]]['working_keys'])

	elif bot.verify_context_message(message, 'stop_tacking', 'да'):
		db_handler.delete_user(message["chat"]["id"])
		bot.send_message("Отслеживание остановлено. Снова начать отслеживать задачи можно если набрать комманду /start", message["chat"]["id"])
		bot.context.pop(message["chat"]["id"], None)
	
	else:
		logger.debug(f'Got random message from @{message["from"]["username"]}, id{message["from"]["id"]}{" in chat " + str(message["chat"]["id"]) if message["chat"]["type"] == "group" else ""}, {message["chat"]["title"] if message["chat"]["type"] == "group" else message["chat"]["type"]}, with text "{message["text"]}"')
		bot.send_message('Не понимаю эту команду', message["chat"]["id"])


def bot_listener():
	bot.polling()

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


if __name__ == '__main__':
	os.system('cls' if os.name=='nt' else 'clear')
	logger.debug('Started')
	
	inline_argument = args.part.pop()
	if inline_argument == 'parser':
		parser()
	elif inline_argument == 'bot':
		bot_listener()
	else:
		with concurrent.futures.ThreadPoolExecutor() as executor:
			threads = [executor.submit(parser), executor.submit(bot_listener)]

			for f in concurrent.futures.as_completed(threads):
				f.result()
