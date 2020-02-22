import os
from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import log_parser
import db_handler


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_TOKEN')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'


@app.route('/')
def home():
	cl = log_parser.get_current_log()
	lt = log_parser.get_last_telegram_response(cl)
	lp = log_parser.get_last_parsing(cl)
	nt = log_parser.get_new_tasks_q(cl)
	st = log_parser.get_sent_tasks_q(cl)

	try:
		proc_sent = [st[hostname] / nt[hostname] * 100 for hostname in st]
	except ZeroDivisionError:
		proc_sent = 0

	return render_template('home.html', title='Parsing Stats', lt=lt, lp=lp, nt=nt, st=st, proc_sent=proc_sent)

@app.route('/users')
def users():
	cl = log_parser.get_current_log()
	sm = log_parser.get_sent_messages(cl)
	users = db_handler.get_users()
	return render_template('users.html', title='Users stats', sm=sm, users=users)