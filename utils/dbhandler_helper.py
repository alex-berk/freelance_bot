import sqlite3

class DBHandler:
	def __init__(self, db_loc):
		self.db_loc = db_loc

	def __repr__(self):
		return f'{self.__class__.__name__}("{self.db_loc}")'

	def create_db(self):
		conn = sqlite3.connect(self.db_loc)
		cursor = conn.cursor()
		try:
			cursor.execute('''CREATE TABLE users(
								id integer primary key,
								search_keys text,
								lang text NOT NULL DEFAULT 'rus',
								nickname text,
								active integer NOT NULL DEFAULT 1
							)''')

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
		finally:
			conn.close()

	def query_db(self, query, values=''):
		conn = sqlite3.connect(self.db_loc)
		with conn:
			cursor = conn.cursor()
			cursor.execute(query, values)
			return cursor

	def add_user(self, user_id, keys, username, lang):
		keys = ';'.join([''] + keys + [''])
		self.query_db('INSERT INTO users(id, search_keys, nickname, lang, active) VALUES (?, ?, ?, ?, 1)', (user_id, keys, username, lang))

	def update_user_keys(self, id, keys):
		self.query_db('UPDATE users SET search_keys=? WHERE id=?', (';'.join([''] + keys + ['']), id))

	def get_users(self):
		cursor = self.query_db("SELECT id, search_keys, lang, nickname, active FROM users")
		return [(User(row[0], row[1].split(";")[1:-1], row[2], row[3], bool(row[4]))) for row in cursor.fetchall()]

	def get_user_status(self, user_id):
		cursor = self.query_db("SELECT active FROM users WHERE id=?", (user_id,))
		return cursor.fetchone()[0]
	def get_user_skeys(self, user_id):
		cursor = self.query_db("SELECT search_keys FROM users WHERE id=?", (user_id,))
		try:
			return cursor.fetchone()[0][1:-1].split(';')
		except TypeError:
			return []

	def get_relevant_users_ids(self, search_keys):
		criteria = ' OR '.join([f"search_keys LIKE \"%;{key};%\"" for key in search_keys])
		cursor = self.query_db("SELECT id FROM users WHERE active=1 AND (" + criteria  + ")")
		results = cursor.fetchall()
		if results:
			return [i[0] for i in results]
		return []

	def delete_user(self, user_id):
		self.query_db("DELETE FROM users WHERE id=?", (user_id,))

	def add_task(self, task):
		task['inline_tags'] = ';'.join(task['tags']) if task['tags'] else ''
		self.query_db("INSERT INTO tasks VALUES (:link, :title, :inline_tags, :price, :price_format)", task)

	def get_task(self, search_id):
		cursor = self.query_db('SELECT * FROM tasks WHERE link=?', (search_id,))
		task = {}
		task['link'], task['title'], task['tags'], task['price'], task['price_format'] = cursor.fetchone()
		return task

	def get_tasks_links(self, q=25):
		cursor = self.query_db('SELECT link FROM tasks ORDER BY link DESC')
		return [i[0] for i in cursor.fetchmany(q)]

	def check_task_link(self, task_link):
		cursor = self.query_db('SELECT link FROM tasks WHERE link=?', (task_link,))
		return bool(cursor.fetchone())

	def update_user_lang(self, user_id, lang):
		self.query_db('UPDATE users SET lang=? WHERE id=?', (lang, user_id))

	def change_user_status(self, user_id, active=0):
		self.query_db('UPDATE users SET active=? WHERE id=?', (active, user_id,))
