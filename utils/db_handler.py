import sqlite3
import logging
from collections import namedtuple

logger = logging.getLogger('__main__')

User = namedtuple('User', ['chat_id', 'keywords', 'lang', 'name', 'active'])

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

try:
	cursor.execute('''CREATE TABLE users(
						id integer primary key,
						search_keys text,
						lang text NOT NULL DEFAULT 'rus',
						nickname text,
						active integer NOT NULL DEFAULT 1,
					)''')
	conn.commit()
except sqlite3.OperationalError:
	pass

try:
	cursor.execute('''CREATE TABLE tasks(
						link text primary key,
						title text,
						tags text,
						price text,
						price_format text
					)''')
	conn.commit()
except sqlite3.OperationalError:
	pass


def add_user(id, keys, username, lang):
	conn = sqlite3.connect('data.db')
	with conn:
		keys = ';'.join([''] + keys + ['']) 
		conn.cursor().execute('INSERT INTO users(id, search_keys, nickname, lang, active) VALUES (?, ?, ?, ?, 1)', (id, keys, username, lang))
		conn.commit()

def update_user_keys(id, keys):
	conn = sqlite3.connect('data.db')
	with conn:
		conn.cursor().execute('UPDATE users SET search_keys=? WHERE id=?', (';'.join([''] + keys + ['']), id))
		conn.commit()

def get_users():
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute("SELECT id, search_keys, lang, nickname, active FROM users")
	return [(User(row[0], row[1].split(";"), row[2], row[3], bool(row[4]))) for row in cursor.fetchall()]

def get_user_skeys(user_id):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute("SELECT search_keys FROM users WHERE id=?", (user_id,))
	try:
		return cursor.fetchone()[0][1:-1].split(';')
	except TypeError:
		return []

def get_relevant_users_ids(search_keys):
	conn = sqlite3.connect('data.db')
	with conn:
		cursor = conn.cursor()
		criteria = ' OR '.join([f"search_keys LIKE \"%;{key};%\"" for key in search_keys])
		cursor.execute("SELECT id FROM users WHERE " + criteria)
		results = cursor.fetchall()
		if results:
			return [i[0] for i in results]
		return []

def delete_user(user_id):
	conn = sqlite3.connect('data.db')
	with conn:
		cursor = conn.cursor()
		cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
		conn.commit()

def add_task(task):
	conn = sqlite3.connect('data.db')
	with conn:
		task['inline_tags'] = ';'.join(task['tags']) if task['tags'] else ''
		try:
			conn.cursor().execute("INSERT INTO tasks VALUES (:link, :title, :inline_tags, :price, :price_format)", task)
			conn.commit()
		except sqlite3.IntegrityError as e:
			logger.error(e)
			raise e

def get_task(search_id):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute('SELECT * FROM tasks WHERE link=?', (search_id,))
	task = {}
	task['link'], task['title'], task['tags'], task['price'], task['price_format'] = cursor.fetchone()
	return task

def get_tasks_links(q=25):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute('SELECT link FROM tasks ORDER BY link DESC')
	return [i[0] for i in cursor.fetchmany(q)]

def check_task_link(task_link):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute('SELECT link FROM tasks WHERE link=?', (task_link,))
	return bool(cursor.fetchone())

def update_user_lang(user_id, lang):
	with conn:
		cursor.execute('UPDATE users SET lang=? WHERE id=?', (lang, user_id))
