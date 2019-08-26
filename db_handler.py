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


def add_user(id, tags):
	conn = sqlite3.connect('data.db')
	with conn:
		conn.cursor().execute('INSERT INTO users VALUES (?, ?)', (id, ';'.join(tags)))
		conn.commit()

def get_users():
	conn = sqlite3.connect('data.db')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM users")
	return [(User(row[0], row[1].split(";"))) for row in cursor.fetchall()]

def add_task(task):
	conn = sqlite3.connect('data.db')
	with conn:
		task['tags'] = ';'.join(task['tags'])
		try:
			conn.cursor().execute("INSERT INTO tasks VALUES (:id, :title, :tags, :price, :price_format)", task)
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
