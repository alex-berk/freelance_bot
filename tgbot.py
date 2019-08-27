import os, logging
import datetime
import requests, json
from telebot import TeleBot
import db_handler

logger = logging.getLogger('__main__')


def parse_string(string):
	word_list = [i.lower() for i in string.split(',')]
	cleaned_list = []
	for word in word_list:
		cleaned_word = ''
		for symb in word:
			if symb.isalpha() or symb.isdigit() or symb == ' ':
				cleaned_word += symb
			else:
				cleaned_word += ' '
		cleaned_word = cleaned_word.strip()
		if cleaned_word: cleaned_list.append(cleaned_word)
	return cleaned_list


class BotNotifier(TeleBot):
	def __init__(self, token, admin_chat_id):
		super().__init__(token)
		self.admin_chat_id = admin_chat_id
		self.setup_step = {}

		@self.message_handler(commands=['status', 'start', 'keywords', 'cancel', 'stop'])
		def handle_commands(message):
			logger.info(f'Got message from @{message.from_user.username}, id{message.from_user.id} in chat {message.chat.id}, {message.chat.type if not message.chat.title else message.chat.title}, with text "{message.text}"')
			if self.verify_command(message.text, 'status'):
				status_text = 'Up and running!'
				if self.setup_step.get(message.chat.id): status_text += '\nCurrent setup step: ' + self.setup_step[message.chat.id]
				self.send_message(status_text, message.chat.id)
			elif self.verify_command(message.text, 'start'):
				self.setup_step[message.chat.id] = None
				if db_handler.get_user_skeys(message.chat.id):
					self.send_message('У вас уже настроены ключевые слова для поиска.\nЗаново их задать можно коммандой /keywords', message.chat.id)
				else:
					self.setup_keys(message.chat.id)
			elif self.verify_command(message.text, 'keywords'):
				self.setup_step[message.chat.id] = None
				self.setup_keys(message.chat.id)
			elif self.verify_command(message.text, 'cancel'):
				self.setup_step[message.chat.id] = None
				self.send_message('Операция отменена', message.chat.id)
			elif self.verify_command(message.text, 'stop'):
				self.setup_step[message.chat.id] = 'stop_tacking'
				self.send_message('Вы точно хотите остановить отслеживание?\n(Напишитие "Да" чтобы подтвердить)', message.chat.id)
			else:
				self.send_message('Я не знаю таких команд', message.chat.id)

		@self.message_handler(content_types=['text'])
		def handle_text(message):
			if self.setup_step.get(message.chat.id) == 'setup_keys':
				s_keys = parse_string(message.text)
				try:
					db_handler.add_user(message.chat.id, s_keys)
				except db_handler.sqlite3.IntegrityError:
					db_handler.update_user_keys(message.chat.id, s_keys)
				confirm_text = 'Все готово. Ваши ключевые слова для поиска:\n<b>' + ", ".join(s_keys) + '</b>\n\nНачинаю отслеживать задачи'
				self.send_message(confirm_text, message.chat.id)
				self.send_sticker('CAADAgADBwIAArD72weq7luNKMN99BYE', message.chat.id)
				self.setup_step[message.chat.id] = None
			elif self.setup_step.get(message.chat.id) == 'stop_tacking':
				if message.text.lower() == 'да':
					db_handler.delete_user(message.chat.id)
					self.send_message("Отслеживание остановлено. Снова начать отслеживать задачи можно если набрать комманду /start", message.chat.id)
					self.setup_step[message.chat.id] = None
			else:
				logger.debug(f"Got random message {message}")

	def verify_command(self, text, command):
		return text == '/' + command or text == ''.join(['/', command, '@', self.get_me().username])

	def send_message(self, message, chat_id=None, link=None, disable_preview=False):
		logger.debug(f"Sending message to {chat_id}")
		if not chat_id: chat_id = self.admin_chat_id
		params = {'chat_id': chat_id, 'text': message, 'parse_mode':'html', 'disable_web_page_preview': disable_preview}
		if link:
			try:
				anchor, url = link
			except ValueError:
				anchor, url = ('Просмотреть', link)
			params['reply_markup'] = json.dumps({'inline_keyboard': [[{'text': anchor, 'url': url}]]})
		r = requests.post(f'https://api.telegram.org/bot{self.token}/sendMessage', params=params)
		if not json.loads(r.text)['ok']:
			logger.error(f"Message not been sent!, Got response: {r.text}; {chat_id}; {link}; {disable_preview}")

	def send_sticker(self, sticker_id, chat_id=None):
		try:
			if not chat_id: chat_id = self.admin_chat_id
			params = {'chat_id': chat_id, 'sticker': sticker_id}
			r = requests.post(f'https://api.telegram.org/bot{self.token}/sendSticker', params=params)
		except Exception as e:
			logger.error(e)

	def send_job(self, job, chat_id=None):
		logger.debug(f"Sending job {job['id']}")
		tags = ', '.join(job['tags'])
		price = job['price'] + ' <i>за час</i>' if job['price_format'] == 'per_hour' else job['price']
		text = f"<b>{job['title']}</b>\n{price}\n<code>{tags}</code>"
		self.send_message(text, link=job['url'], chat_id=chat_id, disable_preview=True)

	def setup_keys(self, chat_id):
		self.setup_step[chat_id] = 'setup_keys'
		setup_text = 'Сейчас можно будет задать ключевые слова для поиска.\nКаждый раз, когда бот будет находить их в названии, вам придет оповещение.\nКлючи разделяются запятой.\nДопускается использование только букв, символов и пробелов\n<code>Пример:</code>\n<code>node js, js, фронтенд</code>\nПоиск осуществляется по тегам и отдельным словам из заголовков, так что лучше задавать однословные ключи.\nОтменить настройку можно командой /cancel'
		current_keys = db_handler.get_user_skeys(chat_id)
		self.send_message(setup_text, chat_id)
		if current_keys: self.send_message(f'Ваши текущие ключевые слова для поиска:\n<b>{", ".join(current_keys)}</b>', chat_id)
