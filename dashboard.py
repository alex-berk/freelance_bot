import os
from flask import Flask, render_template, url_for, request, jsonify, redirect, flash
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from utils import DBHandler, log_parser, parse_string


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_TOKEN')
bcrypt = Bcrypt()
login_manager = LoginManager()
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

db_handler = DBHandler('data.db')

@login_manager.user_loader
def load_user(user_id):
	return User.get(user_id)

class User(UserMixin):
	users = {0: None}

	def __init__(self, username, password):
		super().__init__()
		self.username = username
		self.password = bcrypt.generate_password_hash(password).decode('utf-8')
		self.id = max(self.users) + 1
		self.users[self.id] = self

	def get_id(self):
		return self.id

	@classmethod
	def get(cls, id):
		return cls.users.get(id, None)

user_login = os.environ.get('DASHBOARD_LOGIN')
user_pass = os.environ.get('DASHBOARD_PASS')
User(user_login, user_pass)

def dashboard_graph_stats(site_filter):
	if site_filter == 'Total':
		site_filter = None
	ntdy = log_parser.get_new_tasks_q_wdays(site=site_filter)
	stdy = log_parser.get_sent_tasks_q_wdays(site=site_filter)

	proc_sent_graph = list( map(lambda x, y: round((x[1] / y[1]) * 100, 2), sorted(stdy.items()), sorted(ntdy.items())) )
	ntdy = [i[1] for i in sorted(ntdy.items())]
	stdy = [i[1] for i in sorted(stdy.items())]
	return {'ntdy': ntdy, 'stdy': stdy, 'proc_sent_graph': proc_sent_graph}

def dashboard_table_refresh(site_filter):
	if site_filter == 'Total':
		st = sum(log_parser.get_sent_tasks_q().values())
		nt = sum(log_parser.get_new_tasks_q().values())
		lp = '--'
	else:
		st = log_parser.get_sent_tasks_q(site=site_filter)
		nt = log_parser.get_new_tasks_q(site=site_filter)
		lp = log_parser.get_last_parsing(site=site_filter)
	ltr = log_parser.get_last_telegram_response()
	return {'st': st, 'nt':nt, 'lp': lp, 'ltr': ltr}

def get_dashboard_data():
	lt = log_parser.get_last_telegram_response()
	lp = log_parser.get_last_parsing()
	nt = log_parser.get_new_tasks_q()
	st = log_parser.get_sent_tasks_q()
	ntdy = log_parser.get_new_tasks_q_wdays()
	stdy = log_parser.get_sent_tasks_q_wdays()

	composed = {k:(v, stdy.get(k, 0)) for (k, v) in ntdy.items()}
	composed = {k:(v[0], v[1], round((v[1]/v[0])*100, 2)) for (k, v) in composed.items()}

	proc_sent_graph = list( map(lambda x, y: round((x[1] / y[1]) * 100, 2), sorted(stdy.items()), sorted(ntdy.items())) )

	legend_days = [i[0] for i in sorted(ntdy.items())]
	legend_days = composed.keys()
	wnt = [i[1] for i in sorted(ntdy.items())]
	wst = [i[1] for i in sorted(stdy.items())]

	proc_sent = {hostname: st.get(hostname, 0) / nt[hostname] * 100 if nt[hostname] != 0 else 0 for hostname in nt}

	snt = sum(nt.values())
	sst = sum(st.values())

	return {'lt':lt, 'lp':lp, 'nt':nt, 'st':st, 'proc_sent':proc_sent, 'wnt':wnt, 'wst':wst, 'legend_days':legend_days, 'proc_sent_graph':proc_sent_graph, 'snt':snt, 'sst':sst}


@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		site_filter = request.json.get('site_filter')
		if request.json.get('target') == 'graph':
			data = dashboard_graph_stats(site_filter)
			return jsonify(data)
		elif request.json.get('target') == 'refresh':
			data = dashboard_table_refresh(site_filter)
			return jsonify(data)
		return '', 204

	data = get_dashboard_data()
	return render_template('home.html', title='Parsing Stats', **data)

@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
	if request.method == 'POST':
		if request.form:
			user = request.form['user']
			keywords = parse_string(request.form['keywords'], sep=",")
			db_handler.update_user_keys(user, keywords)
			return redirect(url_for('users'))
		elif request.json:
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

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.get(1)
		if form.login.data.lower() == user.username.lower() and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page or url_for('home'))
		else:
			flash('Check your username and password', 'danger')
	return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))
