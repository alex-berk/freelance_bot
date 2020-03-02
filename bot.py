import os
from utils.tgapi import TgBot
from utils import parse_string, db_handler, log_parser
import logging

logger = logging.getLogger('__main__')

bot = TgBot(os.environ.get('BOT_TOKEN'), os.environ.get('CHAT_ID'))

import loc

for chat_id, pref in loc.preferences.items():
	bot.context[chat_id] = {'lang': pref}

def get_loc_text(text_name, chat_id):
	return loc.msgs[text_name][bot.context[chat_id]['lang']]

def setup_keys(chat_id):
	current_keys = db_handler.get_user_skeys(chat_id)
	if current_keys and bot.context.get(chat_id) != 'setup_keys_replace':
		bot.set_context(chat_id, 'setup_keys')
		msg = get_loc_text('current_keywords', chat_id).format(", ".join(current_keys))
		bot.send_message(msg, chat_id, keyboard=([get_loc_text('button_add', chat_id), get_loc_text('button_replace', chat_id), get_loc_text('button_delete', chat_id), get_loc_text('button_cancel', chat_id)], 3))
	else:
		bot.set_context(chat_id, 'setup_keys_init')
		setup_text = get_loc_text('setup_keywords', chat_id)
		bot.send_message(setup_text, chat_id, keyboard=[get_loc_text('button_cancel', chat_id)])

def confirm_keys_setup(chat_id, s_keys):
	confirm_text = 'Все готово. Ваши ключевые слова для поиска:\n<b>' + ", ".join(s_keys) + '</b>\n\nНачинаю отслеживать задачи'
	bot.send_message(confirm_text, chat_id)
	bot.send_sticker('CAADAgADBwIAArD72weq7luNKMN99BYE', chat_id)
	bot.set_context(chat_id, None)

def setup_language(chat_id):
	bot.set_context(chat_id, 'setup_language')
	bot.context.get(chat_id, {}).get('lang', 'ru')
	msg = 'Выберите язык'
	bot.send_message(msg, chat_id, keyboard=['🇷🇺 Русский', '🇺🇸 English'])

@bot.commands_handler
def handle_commands(message):
	logger.debug('Got message ' + repr(message))
	
	if bot.verify_command(message.text, 'status'):
		print(bot.context)
		status_text = 'Up and running!'
		if message.chat_id == bot.admin_chat_id:
			ltg = log_parser.get_last_telegram_response()
			lp = log_parser.get_last_parsing()
			lp_s = ''.join([f'{k}: {v}\n' for (k, v) in lp])
			nt = log_parser.get_new_tasks_q()
			nt_s = '\n'.join([f'{k}: {v}' for (k, v) in nt.items()])
			status_text = f"\n<b>Last Telegram Response:</b>{ltg}\n\n<b>Last Parsing:</b>\n{lp_s}\n<b>Found Tasks Today:</b>\n{nt_s}\n"
		if bot.context.get(message.chat_id, {'name': None})['name']:
			status_text += '\n<b>Current setup step:</b> ' + bot.context[message.chat_id]['name']
		bot.send_message(status_text, message.chat_id, disable_preview=True)
	
	elif bot.verify_command(message.text, 'start'):
		if db_handler.get_user_skeys(message.chat_id):
			bot.send_message('У вас уже настроены ключевые слова для поиска.\nЗаново их задать можно коммандой /keywords', message.chat_id)
		else:
			setup_keys(message.chat_id)
	
	elif bot.verify_command(message.text, 'keywords'):
		setup_keys(message.chat_id)

	elif bot.verify_command(message.text, 'language'):
		setup_language(message.chat_id)

	elif bot.verify_command(message.text, 'stop'):
		bot.set_context(message.chat_id, 'stop_tacking')
		bot.send_message('Вы точно хотите остановить отслеживание?', message.chat_id, keyboard=['Да', 'Нет'])

	elif bot.verify_command(message.text, 'cancel'):
		bot.set_context(message.chat_id, None)
		bot.send_message('Действие отменено', message.chat_id)
	
@bot.message_handler
def handle_text(message):
	if message.text.lower() in ['нет', get_loc_text('button_cancel', message.chat_id)]:
		if bot.context.get(message.chat_id, None):
			bot.set_context(message.chat_id, None)
			bot.send_message('Действие отменено', message.chat_id)
		else:
			bot.send_message('Нечего отменить', message.chat_id)
	
	elif bot.verify_context_message(message, 'setup_keys', get_loc_text('button_add', message.chat_id)):
		bot.set_context(message.chat_id, 'setup_keys_add')
		bot.send_message(f'Напишите через запятую слова, которые нужно добавить к вашему списку', message.chat_id, keyboard=[get_loc_text('button_cancel', message.chat_id)])

	elif bot.verify_context_message(message, 'setup_keys', get_loc_text('button_replace', message.chat_id)):
		bot.set_context(message.chat_id, 'setup_keys_replace')
		bot.send_message(f'Напишите слова, которыми нужно заменить существующие', message.chat_id, keyboard=[get_loc_text('button_cancel', message.chat_id)])

	elif bot.verify_context_message(message, 'setup_keys', get_loc_text('button_delete', message.chat_id)):
		bot.set_context(message.chat_id, 'setup_keys_delete')
		bot.context[message.chat_id]['working_keys'] = db_handler.get_user_skeys(message.chat_id)
		bot.send_message(f'Напишите слова, которые нужно удалить через запятую или выберете их внизу, на выпадающей клавиатуре', message.chat_id, keyboard=[get_loc_text('button_done', message.chat_id), get_loc_text('button_cancel', message.chat_id)] + bot.context[message.chat_id]['working_keys'])

	elif bot.verify_context_message(message, 'setup_keys_add'):
		s_keys_old = db_handler.get_user_skeys(message.chat_id)
		s_keys_new = [key for key in parse_string(message.text, sep=',') if key not in s_keys_old]
		s_keys = s_keys_old + s_keys_new
		db_handler.update_user_keys(message.chat_id, s_keys)
		confirm_keys_setup(message.chat_id, s_keys)
	
	elif bot.verify_context_message(message, 'setup_keys_init') or bot.verify_context_message(message, 'setup_keys_replace'):
		s_keys = parse_string(message.text, sep=',')
		try:
			db_handler.add_user(message.chat_id, s_keys)
		except db_handler.sqlite3.IntegrityError:
			db_handler.update_user_keys(message.chat_id, s_keys)
		confirm_keys_setup(message.chat_id, s_keys)
	
	elif bot.verify_context_message(message, 'setup_keys_delete'):
		msg_words = parse_string(message.text.lower(), ',')
		if msg_words == ['готово']:
			db_handler.update_user_keys(message.chat_id, bot.context[message.chat_id]['working_keys'])
			confirm_keys_setup(message.chat_id, bot.context[message.chat_id]['working_keys'])
			bot.set_context(message.chat_id, None)
		else:
			for word in msg_words:
				try:
					bot.context[message.chat_id]['working_keys'].remove(word)
					bot.send_message(f'Удалил <b>{word}</b>\nКогда закончите, нажмите "Готово" для того чтобы применить изменения.' , message.chat_id, keyboard=[get_loc_text('button_done', chat_id), get_loc_text('button_cancel', message.chat_id)] + bot.context[message.chat_id]['working_keys'])
				except ValueError:
					bot.send_message(f'Не нашёл слова <b>{word}</b>' , message.chat_id, keyboard=[get_loc_text('button_done', chat_id), get_loc_text('button_cancel', message.chat_id)] + bot.context[message.chat_id]['working_keys'])

	elif bot.verify_context_message(message, 'setup_language'):
		msg_words = parse_string(message.text.lower()).pop()
		if msg_words == "русский":
			bot.context[message.chat_id]['lang'] = 'rus'
			bot.send_message('Установлен русский язык', message.chat_id)
			bot.set_context(message.chat_id, None)
		elif  msg_words == "english":
			bot.context[message.chat_id]['lang'] = 'eng'
			bot.send_message('English language chosen', message.chat_id)
			bot.set_context(message.chat_id, None)
		else:
			bot.send_message('I don\'t know this language')
			bot.setup_language(message.chat_id)

	elif bot.verify_context_message(message, 'stop_tacking', 'да'):
		db_handler.delete_user(message.chat_id)
		bot.send_message("Отслеживание остановлено. Снова начать отслеживать задачи можно если набрать комманду /start", message.chat_id)
		bot.set_context(message.chat_id, None)
	
	else:
		logger.debug('Got random message ' + message.text)
		bot.send_message('Не понимаю эту команду', message.chat_id)

