from dashboard import app
from flask import render_template, url_for
from dashboard import log_parser



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
