import os, logging
import datetime
import requests, json

logger = logging.getLogger('__main__')


class BotNotifier():
	
	def __init__(self, token, admin_chat_id):
		self.token = token
		self.admin_chat_id = admin_chat_id
		self.username = self.call_tg_api('getMe')["result"]["username"]
		self.context = {}
		self.handlers = {}


	def call_tg_api(self, method, params={}, timeout=60):
		url = f'https://api.telegram.org/bot{self.token}/{method}'
		try:
			r = requests.post(url, params=params, timeout=timeout)
		except requests.exceptions.ReadTimeout:
			logger.debug('Timeout')
			self.call_tg_api(method, params, timeout)
		response = json.loads(r.text)
		return response

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
		
		tg_response = self.call_tg_api('sendMessage', params)
		if not tg_response['ok']:
			logger.error(f"Message not been sent!, Got response: {tg_response}; {chat_id}; {link}; {disable_preview}")
			return tg_response["error_code"]
		else:
			return 200

	def send_sticker(self, sticker_id, chat_id=None):
		if not chat_id: chat_id = self.admin_chat_id
		params = {'chat_id': chat_id, 'sticker': sticker_id}
		self.call_tg_api('sendSticker', params)

	def verify_command(self, text, command):
		return text == '/' + command or text == ''.join(['/', command, '@', self.username])

	def verify_context_message(self, message, step_name=None, message_text=None):
		if step_name:
			step_result = self.context.get(message["chat"]["id"], {'name': None})['name'] == step_name
		else:
			step_result = True
		if message_text:
			message_result = message["text"].lower() == message_text
		else:
			message_result = True
		return step_result and message_result


	def message_handler(self, handler_func):
		self.handlers['message_handler'] = handler_func 

	def commands_handler(self, handler_func):
		self.handlers['commands_handler'] = handler_func

	def polling(self, update_id=None):
		params = {'timeout': 60}
		if update_id:
			params['offset'] = update_id + 1
		logger.debug('Sending request to the Telegram server')
		tg_response = self.call_tg_api('getUpdates', params, timeout=100)
		logger.debug('Got response from the Telegram server')
		if tg_response['result']:
			resp = tg_response['result'].pop()
			if resp['message']['text'][0] == '/':
				self.handlers['commands_handler'](resp['message'])
			else:
				self.handlers['message_handler'](resp['message'])
			self.polling(resp['update_id'])
		else:
			self.polling(update_id)

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
