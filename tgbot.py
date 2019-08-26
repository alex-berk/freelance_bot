import os, logging
import datetime
import requests, json
import telebot
import db_handler

logger = logging.getLogger('__main__')


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

class BotNotifier():
	def __init__(self, token, admin_chat_id):
		self.token = token
		self.admin_chat_id = admin_chat_id

		self.listener = telebot.TeleBot(self.token)
		self.setup_step = None

		@self.listener.message_handler(commands=['status', 'start', 'settings', 'cancel', 'stop'])
		def handle_commands(message):
			logger.info(f'Got message from @{message.from_user.username}, id{message.from_user.id} in chat {message.chat.id}, {message.chat.type if not message.chat.title else message.chat.title}, with text "{message.text}"')
			if message.text == '/status':
				status_text = 'Up and running!'
				if self.setup_step: status_text += '\nCurrent setup step: ' + self.setup_step
				self.send_message(status_text, message.chat.id)
			elif message.text == '/start':
				user_skeys = db_handler.get_user_skeys(message.chat.id)
				if user_skeys:
					self.send_message('У вас уже настроены ключи для поиска:\n<code>' + ', '.join(user_skeys) + '</code>\nЗаново их задать можно коммандой /settings', message.chat.id)
				else:
					self.setup_keys(message.chat.id)
			elif message.text == '/settings':
				self.setup_keys(message.chat.id)
			elif message.text == '/cancel':
				self.setup_step = None
				self.send_message('Операция отменена', message.chat.id)
			elif message.text == '/stop':
				self.setup_step = 'stop_tacking'
				self.send_message('Вы точно хотите остановить отслеживание?\n(Напишитие "Да" чтобы подтвердить)', message.chat.id)
			else:
				self.send_message('Я не знаю таких команд', message.chat.id)

		@self.listener.message_handler(content_types=['text'])
		def handle_text(message):
			if self.setup_step == 'setup_keys':
				s_keys = string_cleaner(message.text)
				try:
					db_handler.add_user(message.chat.id, s_keys)
				except db_handler.sqlite3.IntegrityError:
					db_handler.update_user_keys(message.chat.id, s_keys)
				confirm_text = 'Все готово. Ваши ключи для поиска:\n<code>' + ", ".join(s_keys) + '</code>'
				self.send_message(confirm_text, message.chat.id)
				self.setup_step = None
			elif self.setup_step == 'stop_tacking':
				if message.text.lower() == 'да':
					db_handler.delete_user(message.chat.id)
					self.send_message("Отслеживание остановлено. Снова начать отслеживать задачи можно если набрать комманду /start", message.chat.id)

	def send_message(self, message, chat_id=None, link=None, disable_preview=False):
		if not chat_id: chat_id = self.admin_chat_id
		params = {'chat_id': chat_id, 'text': message, 'parse_mode':'html', 'disable_web_page_preview': disable_preview}
		if link:
			try:
				anchor, url = link
			except ValueError:
				anchor, url = ('Просмотреть', link)
			params['reply_markup'] = json.dumps({'inline_keyboard': [[{'text': anchor, 'url': url}]]})
		r = requests.post(f'https://api.telegram.org/bot{self.token}/sendMessage', params=params)
		success = json.loads(r.text)['ok']
		if success:
			logger.debug(f"Sent message to {chat_id}")
		else:
			logger.error(f"Message not been sent!, Got response: {r.text}; {chat_id}; {link}; {disable_preview}")
		return success

	def send_job(self, job, chat_id=None):
		tags = ', '.join(job['tags'])
		price = job['price'] + ' <i>за час</i>' if job['price_format'] == 'per_hour' else job['price']
		text = f"<b>{job['title']}</b>\n{price}\n<code>{tags}</code>"
		self.send_message(text, link=job['url'], chat_id=chat_id)
		logger.debug(f"Sent job {job['id']}")

	def setup_keys(self, chat_id):
		self.setup_step = 'setup_keys'
		setup_text = 'Сейчас можно будет задать слова для поиска.\nКаждый раз, когда бот будет находить их в названии, вам придет оповещение\nОтменить настройку можно командой /cancel'
		self.send_message(setup_text, chat_id)
