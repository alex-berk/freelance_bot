import os
import json
from collections import namedtuple, Counter

event = namedtuple('event', ['time', 'module', 'level', 'event'])


def get_current_log():
	logs = os.listdir('logs')
	current_log = sorted(os.listdir('logs')).pop()

	with open('logs/' + current_log, 'r') as log_file:
		log_lines = log_file.readlines()
		log = [line[:-1].split(':',3) for line in log_lines]
		log = [event(*line) for line in log]

	return log

def get_logs_for_period(q=7, s=1):
	logs = os.listdir('logs')
	current_week_log = sorted(os.listdir('logs'), reverse=True)[s:s+q]

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
		if line.event[:23] == 'Sending request to http':
			hosts.add(line.event[19:])
	return hosts

def get_last_parsing(log=None):
	if not log:
		log = get_current_log()
	hosts_time = []
	for host in get_all_hosts(log):
		for line in log[::-1]:
			if line.event == 'Parsed ' + host:
				hosts_time.append((host[8:], line.time))
				break
	return hosts_time

def get_new_tasks_q(log=None):
	if not log:
		log = get_current_log()
	new_tasks = []
	new_task_lines = [line.event[10:] for line in log if line.event[:9] == 'New tasks' and line.event != 'New tasks []']
	for line in new_task_lines:
		new_tasks.extend(json.loads(line.replace('\'', '"')))
	hosts = Counter()
	for task in new_tasks:
		hosts[task.split('/')[2]] += 1
	return hosts

def get_new_tasks_q_wdays(log=None):
	if not log:
		log = get_logs_for_period()
	new_tasks = []
	new_task_lines = [line.time.split(';')[0] for line in log if line.event.startswith('Sending task') and line.event.endswith('to db')]
	hosts = Counter()
	hosts.update(new_task_lines)
	return hosts

def get_sent_tasks_q(log=None):
	if not log:
		log = get_current_log()
	sent_tasks = []
	sent_task_lines = [line.event.split('\'')[1] for line in log if line.event[:10] == 'Found task']
	tasks = Counter()
	tasks.update([line.split('/')[2] for line in sent_task_lines])
	return tasks

def get_sent_tasks_q_wdays(log=None):
	if not log:
		log = get_logs_for_period()
	sent_tasks = []
	sent_task_lines = [line.time.split(';')[0] for line in log if line.event.startswith('Found task')]
	tasks = Counter()
	tasks.update([line for line in sent_task_lines])
	return tasks

def get_sent_messages(log=None):
	if not log:
		log = get_current_log()
	users = Counter()
	sent_tasks = []
	sent_task_lines = [line.event.split('for the users ')[1] for line in log if line.event[:10] == 'Found task']
	users_ids = [id[1:-1].split(', ') for id in sent_task_lines]
	users_ids_flatten = [item for sublist in users_ids for item in sublist]
	users.update(users_ids_flatten)
	return users

if __name__ == '__main__':
	lp = get_last_parsing()
	nt = get_new_tasks_q(get_logs_for_period())
	st = get_sent_tasks_q(get_logs_for_period())
	# print(lp)
	# print(nt)
	# print(st)

	print(sorted(get_new_tasks_q_wdays().items()))
	# (l1, l2) = sorted(get_sent_tasks_q_wdays().items())
	print([i[0] for i in sorted(get_sent_tasks_q_wdays().items())])
