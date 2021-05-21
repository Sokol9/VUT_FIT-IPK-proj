#!usr/bin/python3

#########################
#implementation fileget.py script
#autor: Jakub Sokolik (xsokol14)
#30.3.2021
#########################

import socket
import sys
import re
import os
import getopt

# funkcia get_port vytvori NSP spojenie a vrati hodnotu portu, cey ktory sa pripojime na server
def get_port(host, port, name):
	sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

	msg = str.encode("WHEREIS " + name)
	adress = (host, port)

	try:
		sock.sendto(msg, adress)
		answer = sock.recvfrom(1024)
		sock.close()
	except NSP.Error:
		sys.stderr.write("problem with NSP connect\n")
		exit(1)

	answer = answer[0].decode('Utf-8')

	match = re.search( 'ERR', answer)
	if match:
		match = re.match( 'ERR (.*)', answer)
		sys.stderr.write(match.group(1) + "\n")
		exit(1)

	match = re.match( r'OK ([\d\.]*):(\d*)',answer)
	file_server_port =int( match.group(2))

	return file_server_port

def get_file(host, port, server_name, file):
	buffer = 1024

	sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
	adress = (host, port)
	msg = str.encode("GET {} FSP/1.0\r\nHostname: {}\r\nAgent: xsokol14\r\n\r\n".format(file, server_name))

	try:
		sock.connect(adress)
		sock.sendall(msg)
		answer = sock.recv(buffer).decode('Utf-8')
	except FSP.error:
		sys.stderr.write("problem with FSP connect\n")
		exit(1)

	#CATCH HEADER
	match = re.search('Bad Request', answer)
	if match:
		sys.stderr.write("Bad Request to FSP connect\n")
		exit(1)

	match = re.search('Not Found', answer)
	if match:
		sys.stderr.write("file not found\n")
		exit(1)

	match = re.search('Error', answer)
	if match:
		answer = sock.recv(1024).decode('Utf-8')
		sys.stderr.write("Some error: " + answer + "\n")
		exit(1)

	#succes request
	second_line = answer.split('\r\n')[1]
	match = re.match('Length:(\d*)', second_line)

	expected_length = int(match.group(1))
	read_length = 0
	message = b''

	#CATCH BODY
	while (read_length < expected_length):
		answer = sock.recv(1024)
		message += answer
		read_length += buffer


	sock.close()
	return message

def save_file(host, port, server_name, path):
	content = get_file(host, port, server_name, path)

	match = re.search('/', path)
	if match:
		match = re.match('(.*/)([^/]*)', path)
		name = match.group(2)
		way = match.group(1)

		os.makedirs(way, exist_ok = True)
	else:
		name = path
		way = ""


	file = open(way + name, "wb")
	file.write(content)
	file.close()


################ CHECK ARGUMENTS ##################

pattern_server = '^([\d\.]*):(\d*)$'
pattern_file = '^fsp://([\w\-_\.]*)/(.*)$'
argv = sys.argv[1:]

try:
	opts, args = getopt.getopt(argv, "n:f:")
except:
	sys.stderr.write("Invalid arguments\nUsage:\nfileget.py -n <nameserver> -f <surl>\n")
	exit(1)

if len(opts) != 2:
	sys.stderr.write("Invalid arguments\nUsage:\nfileget.py -n <nameserver> -f <surl>\n")
	exit(1)

for k, v in opts:
	if k == "-n":
		match = re.search( pattern_server, sys.argv[2])

		if match:
			match = re.match( pattern_server, sys.argv[2])
		else:
			sys.stderr.write("Invalid server name\n")
			exit(1)

		name_server_host = match.group(1)
		name_server_port = int(match.group(2))
	if k == "-f":
		match = re.search( pattern_file, sys.argv[4])
		if match:
			match = re.match( r'^fsp://([\w\-_\.]*)/(.*)$', sys.argv[4])
		else:
			sys.stderr.write("Invalid file path\n")
			exit(1)

		server_name = match.group(1)
		path = match.group(2)

#################### MAIN ######################

file_server_port = get_port(name_server_host, name_server_port, server_name)


############### GET ALL ################
match = re.search('\*', path)
if match:
	match = re.match('(.*[/]{0,1})(\*)', path)
	way = match.group(1)

	files = get_file(name_server_host, file_server_port, server_name, way + "index").decode('Utf-8').split('\r\n')
	files.pop(-1) #koniec odpovede obsahuje prazdny riadok, cize na konci zoznamu je prazdna polozka

	for file in files:
		save_file(name_server_host, file_server_port, server_name, file)

################ GET ###################
else:
	save_file(name_server_host, file_server_port, server_name, path)


exit(0)
