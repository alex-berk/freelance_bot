# coding=utf-8

import os, logging
from multiprocessing import Process
import time, datetime
import requests
import json
import tgbot
import db_handler

logger = logging.getLogger('__main__')
logger.setLevel(logging.DEBUG)

a_date = datetime.date.today()

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))

logger.addHandler(stream_handler)

def set_file_logger():
	global logger
	try:
		logger.removeHandler(file_handler)
	except UnboundLocalError:
		pass

	if not os.path.exists('logs'): os.mkdir('logs')
	formatter = logging.Formatter('%(asctime)s:%(module)s:%(levelname)s:%(message)s', '%H:%M:%S')
	file_handler = logging.FileHandler(os.path.join('logs', str(a_date) + '.log'))
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
set_file_logger()

bot = tgbot.BotNotifier(os.environ['BOT_TOKEN'], os.environ['CHAT_ID'])

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
			logger.debug(f"Sending task {task['id']}")
			tags = ', '.join(task['tags'])
			price = task['price'] + ' <i>за час</i>' if task['price_format'] == 'per_hour' else task['price']
			text = f"<b>{task['title']}</b>\n{price}\n<code>{tags}</code>"
			bot.send_message(text, link=task['url'], chat_id=user_id, disable_preview=True)

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


def main():
	global a_date
	while True:
		if a_date != datetime.date.today():
			a_date = datetime.date.today()
			set_file_logger()
		new_tasks = [task for task in parse_tasks() if task['id'] not in db_handler.get_tasks_ids() and not db_handler.check_task_id(task['id'])]
		logger.debug(f"New tasks {[task['id'] for task in new_tasks]}")
		for task in new_tasks:
			print(f"{task['title']}, {task['price']}, {task['price_format']}")
			logger.debug(f"Sending task {task['id']} to db")
			db_handler.add_task(task)
		tasks_sender(new_tasks)
		time.sleep(60 * 5)

def subprocess():
	def setup_keys(chat_id):
		bot.setup_step[chat_id] = 'setup_keys'
		setup_text = 'Сейчас можно будет задать ключевые слова для поиска.\nКаждый раз, когда бот будет находить их в задаче, вам придет оповещение.\nКлючи разделяются запятой.\nДопускается использование только букв, цифр и пробелов\nПоиск осуществляется по тегам и отдельным словам из заголовков, так что лучше задавать однословные ключи.\n\n<code>Пример:</code>\n<code>node js, java script, js, фронтенд</code>'
		current_keys = db_handler.get_user_skeys(chat_id)
		if current_keys: bot.send_message(f'Ваши текущие ключевые слова для поиска:\n<b>{", ".join(current_keys)}</b>', chat_id)
		bot.send_message(setup_text, chat_id, force_reply=True, keyboard=['Отмена'])


	@bot.message_handler(commands=['status', 'start', 'keywords', 'cancel', 'stop'])
	def handle_commands(message):
		logger.debug(f'Got message from @{message.from_user.username}, id{message.from_user.id} in chat {message.chat.id}, {message.chat.title if message.chat.title else message.chat.type}, with text "{message.text}"')
		if bot.verify_command(message.text, 'status'):
			status_text = 'Up and running!'
			if bot.setup_step.get(message.chat.id): status_text += '\nCurrent setup step: ' + bot.setup_step[message.chat.id]
			bot.send_message(status_text, message.chat.id)
		
		elif bot.verify_command(message.text, 'start'):
			bot.setup_step[message.chat.id] = None
			if db_handler.get_user_skeys(message.chat.id):
				bot.send_message('У вас уже настроены ключевые слова для поиска.\nЗаново их задать можно коммандой /keywords', message.chat.id)
			else:
				setup_keys(message.chat.id)
		
		elif bot.verify_command(message.text, 'keywords'):
			bot.setup_step[message.chat.id] = None
			setup_keys(message.chat.id)

		elif bot.verify_command(message.text, 'stop'):
			bot.setup_step[message.chat.id] = 'stop_tacking'
			bot.send_message('Вы точно хотите остановить отслеживание?\n(Нажмите "Да" чтобы подтвердить, "Нет" чтобы продолжить получать уведомления)', message.chat.id, force_reply=True, keyboard=['Да', 'Нет'])

		elif bot.verify_command(message.text, 'cancel'):
			bot.setup_step[message.chat.id] = None
			bot.send_message('Действие отменено', message.chat.id)
		
	@bot.message_handler(content_types=['text'])
	def handle_text(message):
		if message.text.lower() in ['нет', 'отмена']:
			if bot.setup_step[message.chat.id]:
				bot.setup_step[message.chat.id] = None
				bot.send_message('Действие отменено', message.chat.id)
			else:
				bot.send_message('Нечего отменить', message.chat.id)
		
		elif bot.setup_step.get(message.chat.id) == 'setup_keys':
			s_keys = parse_string(message.text)
			try:
				db_handler.add_user(message.chat.id, s_keys)
			except db_handler.sqlite3.IntegrityError:
				db_handler.update_user_keys(message.chat.id, s_keys)
			confirm_text = 'Все готово. Ваши ключевые слова для поиска:\n<b>' + ", ".join(s_keys) + '</b>\n\nНачинаю отслеживать задачи'
			bot.send_message(confirm_text, message.chat.id)
			bot.send_sticker('CAADAgADBwIAArD72weq7luNKMN99BYE', message.chat.id)
			bot.setup_step[message.chat.id] = None
		
		elif bot.setup_step.get(message.chat.id) == 'stop_tacking':
			if message.text.lower() == 'да':
				db_handler.delete_user(message.chat.id)
				bot.send_message("Отслеживание остановлено. Снова начать отслеживать задачи можно если набрать комманду /start", message.chat.id)
				bot.setup_step[message.chat.id] = None
		else:
			logger.debug(f'Got random message from @{message.from_user.username}, id{message.from_user.id} in chat {message.chat.id}, {message.chat.title if message.chat.title else message.chat.type}, with text "{message.text}"')

	@bot.callback_query_handler(func=lambda call:True)
	def test_callback(call):
		logger.info(f'Got callback_query {call}')
	

	bot.polling()


if __name__ == '__main__':
	os.system('cls' if os.name=='nt' else 'clear')
	logger.debug('Started')

	process_1 = Process(target=main)
	process_2 = Process(target=subprocess)
	process_1.start()
	process_2.start()
	process_1.join()
	process_2.join()
