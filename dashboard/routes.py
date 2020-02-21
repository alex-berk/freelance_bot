from dashboard import app
from flask import render_template, url_for
from dashboard import log_parser



@app.route('/')
def home():
	cl = log_parser.get_current_log()
	lt = log_parser.search_last_telegram_response(cl)
	return render_template('home.html', lt=lt)

@app.route('/login')
def login():
	return render_template('login.html')
