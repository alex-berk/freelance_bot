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

def get_last_telegram_response(log):
	for line in log[::-1]:
		if line.event == 'Got response from the Telegram server':
			return(line.time)

def get_all_hosts(log):
	hosts = set()
	for line in log:
		if line.event[:23] == 'Sending request to http':
			hosts.add(line.event[19:])
	return hosts

def get_last_parsing(log):
	hosts_time = []
	for host in get_all_hosts(log):
		for line in log[::-1]:
			if line.event == 'Parsed ' + host:
				hosts_time.append((host[8:], line.time))
				break
	return hosts_time

def get_new_tasks_q(log):
	new_tasks = []
	new_task_lines = [line.event[10:] for line in log if line.event[:9] == 'New tasks' and line.event != 'New tasks []']
	for line in new_task_lines:
		new_tasks.extend(json.loads(line.replace('\'', '"')))
	hosts = Counter()
	for task in new_tasks:
		hosts[task.split('/')[2]] += 1
	return hosts

def get_sent_tasks_q(log):
	sent_tasks = []
	sent_task_lines = [line.event.split('\'')[1] for line in log if line.event[:10] == 'Found task']
	tasks = Counter()
	tasks.update([line.split('/')[2] for line in sent_task_lines])
	return tasks

def get_sent_messages(log):
	users = Counter()
	sent_tasks = []
	sent_task_lines = [line.event.split('for the users ')[1] for line in log if line.event[:10] == 'Found task']
	users_ids = [id[1:-1].split(', ') for id in sent_task_lines]
	users_ids_flatten = [item for sublist in users_ids for item in sublist]
	users.update(users_ids_flatten)
	return users

if __name__ == '__main__':
	cl = get_current_log()

	lp = get_last_parsing(cl)
	nt = get_new_tasks_q(cl)
	st = get_sent_tasks_q(cl)
	sm = get_sent_messages(cl)
	print(lp)
	print(nt)
	print(st)
	print(sm['87794324'])
