#!/usr/bin/python3

# Student name and No.: Liao Hsuan-cheng 3035120483
# Student name and No.: Song Yi Ting     3035124829
# Development platform: Mac OS
# Python version: 3.6
# Version: 10

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
# Global variables list
#

USER_STATE = "START"

USER_NAME = ""

# Create a socket for sending messages to the server
USER_SCKT = socket.socket()

# socket list for FORWARD LINK
USER_FSCKT = []

# a dictionary for BACKWARD LINK
# (peer_hashID, peer_socket)
USER_BSCKT = {}

# user ip address
USER_IP = ""

# user port number
USER_PORT = sys.argv[3]

# user chatroom name
USER_ROOM = ""

# a dictionary for members in the same chatroom
# (member_hashID, (name, ip, port, msgid))
USER_MEMBER = {}

# user message ID (starting from 0)
USER_MSGID = 0

# user hash id
USER_HASHID = 0

# a timer object
KEEPALIVE = TimerClass()

# a list of all thread handlers
USER_THREAD = []

# a lock object to protect global variables
gLock = threading.Lock()

# a flag variable to control all threads
all_thread_running = True

# server info
SERVER_IP = 0
SERVER_PORT = 0


#
# End of Global variables
#

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
# Other function calls
#

def check_connection(ip, port):
	try:
		USER_SCKT.connect((SERVER_IP, SERVER_PORT))
	except OSError as e:
		print("[check_connection] OSError: ", e)
		return False
	return True

def set_connection(ip, port):

	return

def hash_list():
	gList = []
	for hid, info in USER_MEMBER.items():
		gList.append(hid)
	return gList.sort()

def p2p_handshake():
	# P:roomname:username:IP:Port:msgID::\r\n
	msg = "P:" + USER_ROOM + ":" + USER_NAME + ":" + USER_IP + ":" + USER_PORT + ":" + USER_MSGID + "::\r\n"
	# send message
	# receive message 
	# no error: get S:msgID::\r\n 	return True
	# error: No response; just close the connection 	return False


# A funtion for sending out JOIN request
def send_join():
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_IP, USER_PORT, USER_ROOM, KEEPALIVE

	# JOIN request -- J:roomname:username:userIP:userPort::\r\n
	join_requ = "J:" + USER_ROOM + ":" + USER_NAME + ":" + USER_IP.getsockname()[0] + ":" + USER_PORT+"::\r\n"
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



def connect_member():

	lst = hash_list()
	
	if len(lst) == 1:
		return
	
	start = lst.index(USER_HASHID)+1
	
	while (lst[start] != USER_HASHID):
		ip = USER_MEMBER[lst[start]][1]
		port = USER_MEMBER[lst[start]][2]
		# if there is a BACKWARD LINK between start and this program
		if lst[start] in USER_MEMBER:
			start = (start+1) % lst.size()
		else:
			# set_connection to lst[start]
			USER_SCKT.connect()
			if:

				if p2p_handshake():
					break
				else:
					start = (start+1) % lst.size()
			else:
				start = (start+1) % lst.size()
	return

#
# End of Other function calls
#

#
# Thread handlers
#

def forward_thd():
	connect_member()

	return

def client_thd(csckt, caddr):

	# get name of thread
	myName = threading.currentThread().name
	
	# Handshaking procedure
	# receive request message
	try:
		rmsg = csckt.recv(500)
	except socket.error as err:
		print("[client_thd] Request message error at thread %s: %s\n" % (myName, err))
		return

	rmsg_seg = rmsg.decode("ascii").split(':')

	if (rmsg_seg[0] != 'P') || (rmsg_seg[1] != USER_ROOM):
		CmdWin.insert(1.0, "\nSome error occured in the hanshaking procedure.")
		return

	# record peer info
	peer_name = rmsg_seg[2]
	peer_ip = rmsg_seg[3]
	peer_port = rmsg_seg[4]
	peer_msgID = rmsg_seg[5]
	peer_hashID = sdbm_hash(peer_name+peer_ip+peer_port)

	# check if the peer is in the chatroom
	gLock.acquire()
	result = USER_MEMBER.get(peer_hashID, "F")
	gLock.release()
	if result == "F":
		# send a join request to room server for the latest member list
		join_resp_decode = send_join()
		if !(peer_name in join_resp_decode):
			print("[client_thd] %s not in member list, terminating connection at thread %s\n" % (peer_name, myName))
			csckt.close()
			return

	# send response message
	gLock.acquire()
	smsg = "S:" + USER_MSGID + "::\r\n"
	csckt.send(smsg.encode("ascii"))
	gLock.release()

	CmdWin.insert(1.0, "\n%s has linked to me" % peer_name)

	# update USER_STATE
	USER_STATE = "CONNECTED"

	# add the new client socket to the USER_BSCKT
	gLock.acquire()
	USER_BSCKT[peer_hashID] = csckt
	gLock.release()

	# set blocking duration to 1.0 second
	cskt.settimeout(1.0)

	# Text flooding
	while all_thread_running:
	
		# wait for any message to arrive
		try:
			rmsg = cskt.recv(500)
		except socket.timeout:
			continue
		except socket.error as err:
			print("[client_thd] Message receiving error at thread %s: %s\n" % (myName, err))
			continue

		# if a message arrived, do the following
		if rmsg:
			CmdWin.insert(1.0,"\nGot a message.")
			
			rmsg_seg = rmsg.decode("ascii").split(':')
			
			if rmsg_seg[0] != 'T':
				print("[client_thd] Message flooding error (not a TEXT message) at thread %s: %s\n" % myName)
				continue
			
			if rmsg_seg[1] != USER_ROOM:
				print("[client_thd] Message flooding error (not the same chatroom) at thread %s: %s\n" % myName)
				continue

			if
			
			
			
			
			
			CmdWin.insert(1.0,"\nRelay it to other peers.")

			gLock.acquire()
			# backward links
			if len(USER_BSCKT) > 1:
				for hid, each_sckt in USER_BSCKT:
					if each_sckt != csckt:
						each_sckt.send(rmsg)
			# forward link
			for each_sckt in USER_FSCKT:
				each_sckt.send(rmsg)
			gLock.release()

		# else a broken connection is detected, do the following
		else:
			print("[client_thd] The peer connection is broken at thread %s\n" % myName)
			
			# remove the backward link
			gLock.acquire()
			del USER_BSCKT[peer_hashID]
			gLock.release()
			break

	# termination
	print("[client_thd] Termination at thread %s\n" % myName)
	return


def listen_thd():

	# create a socket for continuous listening
	listen_sckt = socket.socket()
	
	# inform OS not to hold up the port number and allow us restart the listening thread
	listen_sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# set the server listening socket to have a timeout duration of 1.0 second
	listen_sckt.settimeout(1.0)

	try:
		sockfd.bind((USER_IP, USER_PORT))
	except socket.error as err:
		print("[listen_thd] Socket binding error: ", err)
		sys.exit(1)

	# set socket listening queue
	listen_sckt.listen(5)

	while all_thread_running:
		# wait for incoming connection request
		# however, the socket may unblock after 1.0 second
		try:
			newsckt, caddr = listen_sckt.accept()
		except socket.timeout:
			# raise a timeout exception if the timeout duration has elapsed
			# call accept again without other exception
			continue

		# the system just accepted a new client connection
		print("[listen_thd] A new client has arrived. It is at: \n", caddr)

		# generate a name to this client
		cname = caddr[0]+'_'+str(caddr[1])

		# create and start a new thread to handle this new connection
		cthd = threading.Thread(name=cname, target= client_thd, args=(newsckt,caddr,))
		cthd.start()

		# add this new thread to USER_THREAD list
		USER_THREAD.append(cthd)

	return


#
# End of Thread handlers
#

#
# Functions to handle user input
#

def do_User():
	
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_IP, USER_PORT, USER_ROOM, KEEPALIVE 
	
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
	global USER_STATE, USER_NAME, USER_SCKT, USER_IP, USER_PORT, USER_ROOM, KEEPALIVE 
	
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


def do_Join():
	
	# List out global variables
	global USER_STATE, USER_NAME, USER_SCKT, USER_IP, USER_PORT, USER_ROOM, KEEPALIVE
	
	
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

		# concatenate a string for all of the room members in the room
		gLock.acquire()
		room_member = "\nHere are the members in your chatgroup: "
		count = 1
		index = 2
		# format: userA  A_IP  A_port
		while index < len(join_resp_decode)-2:
			name = join_resp_decode[index]
			ip = join_resp_decode[index+1]
			port = join_resp_decode[index+2]
			room_member += ("\n\t" + str(count) + ": " + group_username)
			room_member += ("\t" + group_userip)
			room_member += ("\t" + group_userport)
			# fill in member information
			hashid = sdbm_hash(name+ip+port)
			USER_MEMBER[hashid] = (name, ip, port,0)
			count += 1
			index += 3
		gLock.release()

		# show chatroom members
		CmdWin.insert(1.0, room_member)

		# start KEEPALIVE timer
		KEEPALIVE.start()

		# create and start a forward thread to select a P2PChat peer for initiating a TCP connection
		fthd = threading.Thread(name="forwardThread", target=forward_thd)
		fthd.start()

		# add the forward thread to the list of thread handlers
		USER_THREAD.append(fthd)

		# create and start a listening thread
		lthd = threading.Thread(name="listenThread", target=listen_thd)
		lthd.start()

		# add the forward thread to the list of thread handlers
		USER_THREAD.append(lthd)




	return

def do_Send():
	CmdWin.insert(1.0, "\nPress Send")
	msg = userentry.get()
	# check if user input is empty
	if msg == "":
		return
	# check if the program has joined or connected to a chatroom program
	if USER_STATE == "JOINED":
		CmdWin.insert(1.0, "\nYou have not yet connect to a chatroom network. Please try again later.")
	if USER_STATE != "CONNECTED":
		CmdWin.insert(1.0, "\nYou have not yet join a chatroom.")
		return

	# T:roomname:originHID:origin_username:msgID:msgLength:Message content::\r\n
	message = "T:"+USER_ROOM+":"+USER_HASHID+":"+USER_NAME+":"+USER_MSGID+":"+str(len(msg))+msg+"::\r\n"
	# send to all members in the member list
	# FORWARD LINK
		# send message
	# BACKWARD LINK
	for hid, tup in USER_BSCKT:
		# send message

	# display message
	CmdWin.insert(1.0, "\n"+USER_NAME+": "+msg)
	


def do_Quit():
	CmdWin.insert(1.0, "\nPress Quit")
	USER_STATE = "TERMINATED"
	KEEPALIVE.stop()
	sys.exit(0)

#
# End of Functions to handle user input
#



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

	# Record server info
	SERVER_IP = sys.argv[1]
	SERVER_PORT = sys.argv[2]
	
	# Connect to the server
	try:
		USER_SCKT.connect((sys.argv[1], int(sys.argv[2])))
		USER_IP = USER_SCKT.getsockname()[0]
		USER_HASHID = sdbm_hash(USER_NAME + USER_IP + USER_PORT)
	except socket.error as cErr:
		CmdWin.insert(1.0, "\nFail to reach the server")
		print("Connection error: ", cErr)
		sys.exit(1)

	win.mainloop()
	

if __name__ == "__main__":
	main()

