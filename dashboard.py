import os
from flask import Flask, render_template, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import log_parser
import db_handler


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_TOKEN')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'


@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		site_filter = request.json.get('site_filter')
		ntdy = log_parser.get_new_tasks_q_wdays(site=site_filter)
		stdy = log_parser.get_sent_tasks_q_wdays(site=site_filter)
		
		proc_sent_graph = list( map(lambda x, y: round((x[1] / y[1]) * 100, 2), sorted(stdy.items()), sorted(ntdy.items())) )
		ntdy = [i[1] for i in sorted(ntdy.items())]
		stdy = [i[1] for i in sorted(stdy.items())]
		return jsonify({'ntdy': ntdy, 'stdy': stdy, 'proc_sent_graph': proc_sent_graph})

	lt = log_parser.get_last_telegram_response()
	lp = log_parser.get_last_parsing()
	nt = log_parser.get_new_tasks_q()
	st = log_parser.get_sent_tasks_q()
	ntdy = log_parser.get_new_tasks_q_wdays()
	stdy = log_parser.get_sent_tasks_q_wdays()

	proc_sent_graph = list( map(lambda x, y: round((x[1] / y[1]) * 100, 2), sorted(stdy.items()), sorted(ntdy.items())) )

	legend_days = [i[0] for i in sorted(ntdy.items())]
	wnt = [i[1] for i in sorted(ntdy.items())]
	wst = [i[1] for i in sorted(stdy.items())]

	proc_sent = {hostname: st.get(hostname, 0) / nt[hostname] * 100 if nt[hostname] != 0 else 0 for hostname in nt}

	return render_template('home.html', title='Parsing Stats', lt=lt, lp=lp, nt=nt, st=st, proc_sent=proc_sent, wnt=wnt, wst=wst, legend_days=legend_days, proc_sent_graph=proc_sent_graph)

@app.route('/users')
def users():
	sm = log_parser.get_sent_messages()
	users = db_handler.get_users()
	return render_template('users.html', title='Users stats', sm=sm, users=users)