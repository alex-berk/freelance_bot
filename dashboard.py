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
	lt = log_parser.get_last_telegram_response()
	lp = log_parser.get_last_parsing()
	nt = log_parser.get_new_tasks_q()
	st = log_parser.get_sent_tasks_q()

	legend_days = [i[0] for i in sorted(log_parser.get_new_tasks_q_wdays().items())]
	wnt = [i[1] for i in sorted(log_parser.get_new_tasks_q_wdays().items())]
	wst = [i[1] for i in sorted(log_parser.get_sent_tasks_q_wdays().items())]

	proc_sent = {hostname: st.get(hostname, 0) / nt[hostname] * 100 if nt[hostname] != 0 else 0 for hostname in nt}

	return render_template('home.html', title='Parsing Stats', lt=lt, lp=lp, nt=nt, st=st, proc_sent=proc_sent, wnt=wnt, wst=wst, legend_days=legend_days)

@app.route('/users')
def users():
	sm = log_parser.get_sent_messages()
	users = db_handler.get_users()
	return render_template('users.html', title='Users stats', sm=sm, users=users)