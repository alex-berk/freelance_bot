import os
import json
from collections import namedtuple, Counter

event = namedtuple('event', ['time', 'module', 'level', 'event'])


log_dir = '../logs/'
def get_current_log():
	logs = os.listdir(log_dir)
	current_log = sorted(os.listdir(log_dir)).pop()

	with open(log_dir + current_log, 'r') as log_file:
		log_lines = log_file.readlines()
		log = [line[:-1].split(':',3) for line in log_lines]
		log = [event(*line) for line in log]

	return log

def get_logs_for_period(q=7, s=1):
	logs = os.listdir(log_dir)
	current_week_log = sorted(os.listdir(log_dir), reverse=True)[s:s+q]

	logs = []
	for log_name in current_week_log:
		with open('logs/' + log_name, 'r') as log_file:
			log_lines = log_file.readlines()
			log = [line[:-1].split(':',3) for line in log_lines]
			log = [event(time=log_name[:-4]+';'+line[0], module=line[1], level=line[2], event=line[3]) for line in log]
			logs.extend(log)
	return logs


def get_last_telegram_response(log=None):
	if not log:
		log = get_current_log()
	for line in log[::-1]:
		if line.event == 'Got response from the Telegram server':
			return(line.time)

def get_all_hosts(log=None):
	if not log:
		log = get_current_log()
	hosts = set()
	for line in log:
		if line.event.startswith('Sending request to http'):
			hosts.add(line.event[19:])
	return hosts

def get_last_parsing(log=None, site=''):
	if not log:
		log = get_current_log()
	hosts_time = []
	if site:
		for line in log[::-1]:
			if 'Parsed' in line.event and site in line.event:
				return line.time
	for host in get_all_hosts(log):
		for line in log[::-1]:
			if line.event == 'Parsed ' + host:
				hosts_time.append((host[8:], line.time))
				break
	return hosts_time

def get_new_tasks_q(log=None, site=''):
	if not log:
		log = get_current_log()
	new_task_lines = [line.event[10:] for line in log if line.event[:9] == 'New tasks' and line.event != 'New tasks []']
	new_tasks = []
	for line in new_task_lines:
		new_tasks.extend(json.loads(line.replace('\'', '"')))
	hosts = Counter()
	for task in new_tasks:
		hosts[task.split('/')[2]] += 1
	if site:
		return hosts[site]
	return hosts

def get_new_tasks_q_wdays(log=None, site=None):
	if not log:
		log = get_logs_for_period()
	new_tasks = []
	if not site:
		new_task_lines = [line.time.split(';')[0] for line in log if line.event.startswith('Sending task') and line.event.endswith('to db')]
	else:
		new_task_lines = [line.time.split(';')[0] for line in log if line.event.startswith('Sending task') and line.event.endswith('to db') and site in line.event]
	hosts = Counter()
	hosts.update(new_task_lines)
	return hosts

def get_sent_tasks_q(log=None, site=''):
	if not log:
		log = get_current_log()
	sent_tasks = []
	sent_task_lines = [line.event.split('\'')[1] for line in log if line.event.startswith('Found task') and site in line.event]
	tasks = Counter()
	tasks.update([line.split('/')[2] for line in sent_task_lines])
	if site:
		return tasks[site]
	return tasks

def get_sent_tasks_q_wdays(log=None, site=None):
	if not log:
		log = get_logs_for_period()
	sent_tasks = []
	if not site:
		sent_task_lines = [line.time.split(';')[0] for line in log if line.event.startswith('Found task')]
	else:
		sent_task_lines = [line.time.split(';')[0] for line in log if line.event.startswith('Found task') and site in line.event]
	tasks = Counter()
	tasks.update([line for line in sent_task_lines])
	return tasks

def get_sent_tasks_list(log=None, user_id=''):
	if not log:
		log = get_current_log()
	sent_tasks_lines = [line.event for line in log if "for the users" in line.event and str(user_id) in line.event]
	sent_tasks = [line.split('\'')[1] for line in sent_tasks_lines]
	return sent_tasks

def get_sent_messages(log=None):
	if not log:
		log = get_current_log()
	users = Counter()
	sent_tasks = []
	sent_task_lines = [line.event.split('for the users ')[1] for line in log if line.event.startswith('Found task')]
	users_ids = [id[1:-1].split(', ') for id in sent_task_lines]
	users_ids_flatten = [int(item) for sublist in users_ids for item in sublist]
	users.update(users_ids_flatten)
	return users
