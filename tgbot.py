import os, logging
import datetime
import requests, json
import telebot

logger = logging.getLogger('__main__')


class BotNotifier():
	def __init__(self, token, admin_chat_id):
		self.token = token
		self.admin_chat_id = admin_chat_id

		self.listener = telebot.TeleBot(self.token)

		@self.listener.message_handler(commands=['start'])
		def handle_start(message):
			logger.info(f'Got message from @{message.from_user.username}, id{message.from_user.id} in chat {message.chat.id}, {message.chat.type if not message.chat.title else message.chat.title}, with text "{message.text}"')
			self.send_message('Started!', message.chat.id)

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

	def send_job(self, job):
		tags = ', '.join(job['tags'])
		price = job['price'] + ' <i>за час</i>' if job['price_format'] == 'per_hour' else job['price']
		text = f"<b>{job['title']}</b>\n{price}\n<code>{tags}</code>"
		self.send_message(text, link=job['url'])
		logger.debug(f"Sent job {job['id']}")


