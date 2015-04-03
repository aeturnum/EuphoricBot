from websocket import create_connection
import json
from time import time
import sys

room_name = 'test'
if __name__ == "__main__":
	if len(sys.argv) > 1:
		if len(sys.argv) > 2:
			print("Usage: python3 ./nick_bot.py <room name> (default room: test)")
			sys.exit(1)
		room_name = sys.argv[1]

ws = create_connection('wss://euphoria.io/room/{}/ws'.format(room_name))
mid = 0

users = {}

def send_ping(ws):
	global mid
	reply = {"type":"ping-reply","data":{"time":int(time())},"id":str(mid)}
	reply = json.dumps(reply)
	ws.send(reply)
	mid += 1

def send_message(ws, message, parent=None):
	global mid
	message = {"type":"send","data":{"content":message,"parent":parent},"id":str(mid)}
	message = json.dumps(message)
	ws.send(message)
	mid += 1

def add_nick(uid, nick):
	global users
	if uid not in users:
		users[uid] = [nick]
	else:
		users[uid].append(nick)

def build_lineage_string(users):
	lineage_strings = []
	for user in users:
		user_string = 'Lineage for {}: {}'.format(user[-1], ' -> '.join(user))
		lineage_strings.append(user_string)

	return '\n'.join(lineage_strings)

while True:
	data = ws.recv()
	
	data = json.loads(data)
	if data['type'] == 'ping-event':
		send_ping(ws)

	if data['type'] == 'send-event':
		content = data['data']['content']
		parent = data['data']['parent']

		if content[0] == '!':
			if content[1:5] == 'echo':
				message = content[5:].strip()
				send_message(ws, message, parent)
			if content[1:8] == 'lineage':
				name = content[8:].strip()

				matching_users = []
				for _, user in users.items():
					current_name = user[-1].lower()
					if current_name.find(name.lower()) >= 0:
						matching_users.append(user)

				if len(matching_users) > 0:
					send_message(ws, build_lineage_string(matching_users), parent)


	if data['type'] == 'nick-event':
		user_id = data['data']['id'].split('-')[0]
		new_nick = data['data']['to']
		add_nick(user_id, new_nick)


	if data['type'] == 'snapshot-event':
		for user in data['data']['listing']:
			user_id = user['id'].split('-')[0]
			nick = user['name']
			add_nick(user_id, nick)