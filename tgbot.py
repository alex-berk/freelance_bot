import os, logging
import datetime
import requests, json
from telebot import TeleBot
import db_handler

logger = logging.getLogger('__main__')


class BotNotifier(TeleBot):
	
	context = {}

	
	def __init__(self, token, admin_chat_id):
		super().__init__(token)
		self.admin_chat_id = admin_chat_id
		self.username = self.get_me().username

	def send_message(self, message, chat_id=None, link=None, callback=None, disable_preview=False, force_reply=False, keyboard=[]):
		logger.debug(f"Sending message to {chat_id}")
		if not chat_id: chat_id = self.admin_chat_id

		reply_markup = {}

		if keyboard:
			force_reply = True
			if type(keyboard[-1]) is int:
				reply_markup['keyboard'] = self.generate_keyboard(*keyboard)
			else:
				reply_markup['keyboard'] = self.generate_keyboard(keyboard)
			reply_markup['resize_keyboard'] = True
			reply_markup['one_time_keyboard'] = True
		else:
			reply_markup['remove_keyboard'] = True

		if link:
			try:
				anchor, url = link
			except ValueError:
				anchor, url = ('Просмотреть', link)
			reply_markup['inline_keyboard'] = [[{'text': anchor, 'url': url}]]
		
		if callback:
			text, data = callback
			reply_markup['inline_keyboard'] = [[{'text': text, 'callback_data': data}]]


		params = {'chat_id': chat_id, 'text': message, 'parse_mode':'html', 'disable_web_page_preview': disable_preview, 'force_reply': force_reply}
		params['reply_markup'] = json.dumps(reply_markup)
		
		r = requests.post(f'https://api.telegram.org/bot{self.token}/sendMessage', params=params)
		if not json.loads(r.text)['ok']:
			if json.loads(r.text)["error_code"] == 403:
				logger.warning(f"Bot was kicked from the chat {chat_id}. Deleting chat from db.")
				db_handler.delete_user(chat_id)
			else:
				logger.error(f"Message not been sent!, Got response: {r.text}; {chat_id}; {link}; {disable_preview}")

	def send_sticker(self, sticker_id, chat_id=None):
		try:
			if not chat_id: chat_id = self.admin_chat_id
			params = {'chat_id': chat_id, 'sticker': sticker_id}
			r = requests.post(f'https://api.telegram.org/bot{self.token}/sendSticker', params=params)
		except Exception as e:
			logger.error(e)

	def verify_command(self, text, command):
		return text == '/' + command or text == ''.join(['/', command, '@', self.username])

	def verify_step_message(self, message, step_name=None, message_text=None):
		if step_name:
			step_result = self.context.get(message.chat.id, {'name': None})['name'] == step_name
		else:
			step_result = True
		if message_text:
			message_result = message.text.lower() == message_text
		else:
			message_result = True
		return step_result and message_result

	@staticmethod
	def generate_keyboard(buttons, row_len=2):
		keyboard, row, counter = [], [], 0
		for button in buttons:
			row.append({'text': button})
			counter += 1
			if counter == row_len:
				keyboard.append(row)
				row, counter = [], 0
		if row: keyboard.append(row)
		return keyboard
