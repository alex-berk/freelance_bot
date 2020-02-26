import os
from flask import Flask, render_template, url_for, request, jsonify, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
import log_parser
import db_handler


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_TOKEN')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'


@app.route('/dashboard', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		site_filter = request.json.get('site_filter')
		if site_filter == 'Total':
			site_filter = None
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

	snt = sum(nt.values())
	sst = sum(st.values())

	return render_template('home.html', title='Parsing Stats', lt=lt, lp=lp, nt=nt, st=st, proc_sent=proc_sent, wnt=wnt, wst=wst, legend_days=legend_days, proc_sent_graph=proc_sent_graph, snt=snt, sst=sst)

@app.route('/users', methods=['GET', 'POST'])
def users():
	if request.method == 'POST':
		user_id = request.json.get('user_id')
		stl = log_parser.get_sent_tasks_list(user_id=user_id)
		return jsonify(stl)

	sm = log_parser.get_sent_messages()
	users = db_handler.get_users()
	return render_template('users.html', title='Users stats', sm=sm, users=users)


class LoginForm(FlaskForm):
	login = StringField('Login', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')

@app.route('/', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		if form.login.data == 'admin' and form.password.data == 'admin':
			return redirect(url_for('home'))
		else:
			flash('Check your username and password', 'danger')
	return render_template('login.html', form=form)