import sqlite3
from collections import namedtuple

User = namedtuple('User', ['chat_id', 'keywords'])

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

try:
	cursor.execute('''CREATE TABLE users(
						id integer,
						search_keys text
					)''')
	conn.commit()
except sqlite3.OperationalError:
	pass


def add_user(id, tags):
	conn = sqlite3.connect('data.db')
	with conn:
		cursor = conn.cursor()
		cursor.execute('INSERT INTO users VALUES (?, ?)', (id, ';'.join(tags)))
		conn.commit()

def get_users():
	conn = sqlite3.connect('data.db')
	cursor.execute("SELECT * FROM users")
	return [(User(row[0], row[1].split(";"))) for row in cursor.fetchall()]
