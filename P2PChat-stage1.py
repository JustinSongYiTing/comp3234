#!/usr/bin/python3

# Student name and No.:
# Student name and No.:
# Development platform:
# Python version:
# Version:


from tkinter import *
import sys
import socket
import threading

# Timer designed for continuously sending JOIN request
class TimerClass(threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		self.event = threading.Event()

	def run(self): 
		while not self.event.is_set():
			send_join()
			self.event.wait(20)

	def stop(self):
		self.event.set()


#
# Global variables
#

USER_STATE = "START"
USER_NAME = ""
# Create a socket for sending messages to the server
USER_SCKT = socket.socket()
# user port number (just for convenience)
USER_PORT = sys.argv[3]
# user chatroom name
USER_ROOM = ""
# a timer object
KEEPALIVE = TimerClass()
# Connect to the server
try:
	USER_SCKT.connect((sys.argv[1], int(sys.argv[2])))
except socket.error as cErr:
	CmdWin.insert(1.0, "\nFail to reach the server")
	print("Connection error: ", cErr)
	sys.exit(1)

#
# This is the hash function for generating a unique
# Hash ID for each peer.
# Source: http://www.cse.yorku.ca/~oz/hash.html
#
# Concatenate the peer's username, str(IP address), 
# and str(Port) to form the input to this hash function
#
def sdbm_hash(instr):
	hash = 0
	for c in instr:
		hash = int(ord(c)) + (hash << 6) + (hash << 16) - hash
	return hash & 0xffffffffffffffff

#
# Functions to handle user input
#

def do_User():
	
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_PORT, USER_ROOM, KEEPALIVE 
	
	# Check state. Only accept request before the user join any chatgroup
	if USER_STATE != "START" and USER_STATE != "NAMED" :
		CmdWin.insert(1.0, "\nYou have already input your username: " + USER_NAME)
		return
	
	# Check if it is an empty entry
	if userentry.get() == "":
		CmdWin.insert(1.0, "\nUsername cannot be empty")
		return

	# Assign entry to USER_NAME
	USER_NAME = userentry.get()
	outstr = "\n[User] username: "+USER_NAME
	CmdWin.insert(1.0, outstr)
	userentry.delete(0, END)

	# Set USER_STATE to NAMED
	USER_STATE = "NAMED"

	return


def do_List():
	
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_PORT, USER_ROOM, KEEPALIVE 
	
	CmdWin.insert(1.0, "\nPress List")

	# Send LIST request to the server
	list_rqt = "L::\r\n"
	USER_SCKT.send(list_rqt.encode("ascii"))

	# Receive LIST answer from the server
	try:
		list_ans = USER_SCKT.recv(500)
	except socket.error as rErr:
		CmdWin.insert(1.0, "\nFail to recieve list from the server")
		print("[do_List] Receive error: ", cErr)
		return

	# Analyze and print the result
	chatrooms = list_ans.decode("ascii").split(':')
	# If no active chatroom, chatrooms = ['G', '', '\r\n']
	if len(chatrooms) == 3:
		CmdWin.insert(1.0, "\nNo active chatroom")
	else:
		room_list = "\nHere are the active chatrooms:"
		i = 1
		while chatrooms[i] != '':
			room_list += ("\n\t" + chatrooms[i])
			i += 1
		CmdWin.insert(1.0, room_list)

	return


# send out JOIN request
def send_join():
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_PORT, USER_ROOM, KEEPALIVE

	# JOIN request -- J:roomname:username:userIP:userPort::\r\n
	join_requ = "J:" + USER_ROOM + ":" + USER_NAME + ":" + USER_SCKT.getsockname()[0] + ":" + USER_PORT+"::\r\n"
	# send a JOIN request to roomserver
	USER_SCKT.send(join_requ.encode("ascii"))

	# check TCP connection

	try:
		join_resp = USER_SCKT.recv(500)
	except socket.error as respErr:
		print("[send_join] Receive error: ", respErr)
		return "error"
	# return the decoded and split response
	return join_resp.decode("ascii").split(':')

def do_Join():
	
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_PORT, USER_ROOM, KEEPALIVE
	
	
	CmdWin.insert(1.0, "\nPress JOIN")

	# user have not yet input username
	if USER_STATE == "START":
		CmdWin.insert(1.0, "\nPlease input your username first")
		userentry.delete(0, END)
		return
	# user already joined a chatroom
	if USER_STATE == "JOINED":
		CmdWin.insert(1.0, "\nYou have already joined a chatroom group: " + USER_ROOM)
		userentry.delete(0, END)
		return

	# get user input
	USER_ROOM = userentry.get()
	# check if user input is empty
	if USER_ROOM == "":
		CmdWin.insert(1.0, "\nRoom name cannot be empty")
		return

	userentry.delete(0, END)

	# send a JOIN request to room server
	join_resp_decode = send_join()

	# when socket error occurs
	if join_resp_decode == "error":
		CmdWin.insert(1.0, "\nFail to join the chatgroup "+ USER_ROOM + " due to unknown server error")
		print("[do_Join] Receive error recieve from send_join")
		return

	# room server responds with an error
	# F:error message::\r\n
	if join_resp_decode[0] == "F":
		CmdWin.insert(1.0, "\nSome error occured in the Room server. Please try again later.")
		CmdWin.insert("\n"+join_resp_decode[1])
		return

	# room server responds normally
	# M:MSID:userA:A_IP:A_port:userB:B_IP:B_port::\r\n
	elif join_resp_decode[0] == "M":
		CmdWin.insert(1.0, "\nSuccessfully joined the chatroom: " + USER_ROOM)
		USER_STATE = "JOINED"

		# representing a string for all of the room members in the room
		room_member = "\nHere are the members in your chatgroup: "
		count = 1
		index = 2
		# display all of the users
		# 1: userA  A_IP  A_port
		while index < len(join_resp_decode)-2:
			group_username = join_resp_decode[index]
			group_userip = join_resp_decode[index+1]
			group_userport = join_resp_decode[index+2]
			room_member += ("\n\t" + str(count) + ": " + group_username)
			room_member += ("\t" + group_userip)
			room_member += ("\t" + group_userport)
			count += 1
			index += 3
		# show chatroom members
		CmdWin.insert(1.0, room_member)
		# start KEEPALIVE timer
		KEEPALIVE.start()

	return

def do_Send():
	CmdWin.insert(1.0, "\nPress Send")


def do_Quit():
	CmdWin.insert(1.0, "\nPress Quit")
	USER_STATE = "TERMINATED"
	KEEPALIVE.stop()
	sys.exit(0)

#
# Set up of Basic UI
#
win = Tk()
win.title("MyP2PChat")

#Top Frame for Message display
topframe = Frame(win, relief=RAISED, borderwidth=1)
topframe.pack(fill=BOTH, expand=True)
topscroll = Scrollbar(topframe)
MsgWin = Text(topframe, height='15', padx=5, pady=5, fg="red", exportselection=0, insertofftime=0)
MsgWin.pack(side=LEFT, fill=BOTH, expand=True)
topscroll.pack(side=RIGHT, fill=Y, expand=True)
MsgWin.config(yscrollcommand=topscroll.set)
topscroll.config(command=MsgWin.yview)

#Top Middle Frame for buttons
topmidframe = Frame(win, relief=RAISED, borderwidth=1)
topmidframe.pack(fill=X, expand=True)
Butt01 = Button(topmidframe, width='8', relief=RAISED, text="User", command=do_User)
Butt01.pack(side=LEFT, padx=8, pady=8);
Butt02 = Button(topmidframe, width='8', relief=RAISED, text="List", command=do_List)
Butt02.pack(side=LEFT, padx=8, pady=8);
Butt03 = Button(topmidframe, width='8', relief=RAISED, text="Join", command=do_Join)
Butt03.pack(side=LEFT, padx=8, pady=8);
Butt04 = Button(topmidframe, width='8', relief=RAISED, text="Send", command=do_Send)
Butt04.pack(side=LEFT, padx=8, pady=8);
Butt05 = Button(topmidframe, width='8', relief=RAISED, text="Quit", command=do_Quit)
Butt05.pack(side=LEFT, padx=8, pady=8);

#Lower Middle Frame for User input
lowmidframe = Frame(win, relief=RAISED, borderwidth=1)
lowmidframe.pack(fill=X, expand=True)
userentry = Entry(lowmidframe, fg="blue")
userentry.pack(fill=X, padx=4, pady=4, expand=True)

#Bottom Frame for displaying action info
bottframe = Frame(win, relief=RAISED, borderwidth=1)
bottframe.pack(fill=BOTH, expand=True)
bottscroll = Scrollbar(bottframe)
CmdWin = Text(bottframe, height='15', padx=5, pady=5, exportselection=0, insertofftime=0)
CmdWin.pack(side=LEFT, fill=BOTH, expand=True)
bottscroll.pack(side=RIGHT, fill=Y, expand=True)
CmdWin.config(yscrollcommand=bottscroll.set)
bottscroll.config(command=CmdWin.yview)

def main():
	if len(sys.argv) != 4:
		print("P2PChat.py <server address> <server port no.> <my port no.>")
		sys.exit(2)

	win.mainloop()
	

if __name__ == "__main__":
	main()

