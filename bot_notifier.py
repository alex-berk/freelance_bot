
import requests, json
import os

class Bot_Notifier():
	def __init__(self, token, admin_chat_id):
		self.token = token
		self.admin_chat_id = admin_chat_id

	def send_message(self, message, url=None, chat_id=None):
		if not chat_id: chat_id = self.admin_chat_id
		params = {'chat_id': chat_id, 'text': message, 'parse_mode':'html', 'disable_web_page_preview': True}
		if url:
			params['reply_markup'] = json.dumps({'inline_keyboard': [[{'text': 'Просмотреть', 'url': url}]]})
		r = requests.post(f'https://api.telegram.org/bot{self.token}/sendMessage', params=params)
		success = json.loads(r.text)['ok']
		if not success:
			print('Message not been sent!, Got response:', r.text, text, url, sep='\n')
		return success
