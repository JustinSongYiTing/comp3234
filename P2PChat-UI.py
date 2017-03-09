#!/usr/bin/python3

# Student name and No.:
# Student name and No.:
# Development platform:
# Python version:
# Version:


from tkinter import *
import sys
import socket

#
# Global variables
#

USER_STATE = "START"
USER_NAME = ""
# Create a socket for sending messages to the server
USER_SCKT = socket.socket()

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
	global USER_STATE, USER_NAME, USER_SCKT
	
	# Check state
	if USER_STATE != "START":
		CmdWin.insert(1.0, "\nInvalid instruction")
		return
	
	# Check if it is an empty entry
	if userentry.get() == "":
		CmdWin.insert(1.0, "\nUser name cannot be empty")
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
	global USER_STATE, USER_NAME, USER_SCKT
	
	CmdWin.insert(1.0, "\nPress List")



	# Send list request to the server
	list_rqt = "L::\r\n"
	USER_SCKT.send(list_rqt.encode("ascii"))

	# Receive list answer from the server
	try:
		list_ans = USER_SCKT.recv(500)
	except socker.error as rErr:
		CmdWin.insert(1.0, "\nFail to recieve list from the server")
		print("Recieve error: ", cErr)
		return

	# Analyze and print the result
	chatrooms = list_ans.decode("ascii").split(':')
	# If no active chatroom, chatrooms = ['G', '', '\r\n']
	if len(chatrooms) == 3:
		CmdWin.insert(1.0, "\nNo active chatroom")
	else:
		CmdWin.insert(1.0, "\nHere are the active chatrooms:")
		i = 1
		while chatrooms[i] != '':
			CmdWin.insert("\n\tchatrooms[i]")
			i = i+1

	return


def do_Join():
	CmdWin.insert(1.0, "\nPress JOIN")


def do_Send():
	CmdWin.insert(1.0, "\nPress Send")


def do_Quit():
	CmdWin.insert(1.0, "\nPress Quit")
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

