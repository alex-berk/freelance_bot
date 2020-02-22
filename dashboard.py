import os
from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import log_parser


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_TOKEN')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


@app.route('/')
def home():
	cl = log_parser.get_current_log()
	lt = log_parser.get_last_telegram_response(cl)
	lp = log_parser.get_last_parsing(cl)
	nt = log_parser.get_new_tasks_q(cl)
	st = log_parser.get_sent_tasks_q(cl)

	return render_template('home.html', lt=lt, lp=lp, nt=nt, st=st)

@app.route('/login')
def login():
	return render_template('login.html')