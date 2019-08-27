import sqlite3
import logging
from collections import namedtuple

logger = logging.getLogger('__main__')

User = namedtuple('User', ['chat_id', 'keywords'])

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

try:
	cursor.execute('''CREATE TABLE users(
						id integer primary key,
						search_keys text
					)''')
	conn.commit()
except sqlite3.OperationalError:
	pass

try:
	cursor.execute('''CREATE TABLE tasks(
						id integer primary key,
						title text,
						tags text,
						price integer,
						price_format text
					)''')
	conn.commit()
except sqlite3.OperationalError:
	pass


def add_user(id, keys):
	conn = sqlite3.connect('data.db')
	with conn:
		conn.cursor().execute('INSERT INTO users VALUES (?, ?)', (id, ';'.join([''] + keys + [''])))
		conn.commit()

def update_user_keys(id, keys):
	conn = sqlite3.connect('data.db')
	with conn:
		conn.cursor().execute('UPDATE users SET search_keys=? WHERE id=?', (';'.join([''] + keys + ['']), id))
		conn.commit()

def get_users():
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM users")
	return [(User(row[0], row[1].split(";"))) for row in cursor.fetchall()]

def get_user_skeys(user_id):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute("SELECT search_keys FROM users WHERE id=?", (user_id,))
	try:
		return cursor.fetchone()[0].split(';')
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
		task['inline_tags'] = ';'.join(task['tags'])
		try:
			conn.cursor().execute("INSERT INTO tasks VALUES (:id, :title, :inline_tags, :price, :price_format)", task)
			conn.commit()
		except sqlite3.IntegrityError as e:
			logger.error(e)
			raise e

def get_task(search_id):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute('SELECT * FROM tasks WHERE id=?', (search_id,))
	task = {}
	task['id'], task['title'], task['tags'], task['price'], task['price_format'] = cursor.fetchone()
	return task

def get_tasks_ids(q=10):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute('SELECT id FROM tasks ORDER BY id DESC')
	return [i[0] for i in cursor.fetchmany(q)]

def check_task_id(task_id):
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute('SELECT id FROM tasks WHERE id=?', (task_id,))
	return bool(cursor.fetchone())
