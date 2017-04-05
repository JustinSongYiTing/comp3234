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
# KEEPALIVE Timer designed for continuously sending JOIN request
#

class KEEPALIVETimerClass(threading.Thread):

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

# server info
SERVER_IP = 0
SERVER_PORT = 0

# user info
USER_STATE = "START"
USER_NAME = ""
# user ip address
USER_IP = ""
# user port number
USER_PORT = sys.argv[3]
# user chatroom name
USER_ROOM = ""
# Create a socket for sending messages to the server
USER_SCKT = socket.socket()

# socket list for FORWARD LINK
USER_FSCKT = []

# a dictionary for BACKWARD LINK
# (peer_hashID, peer_socket)
USER_BSCKT = {}

# a dictionary for members in the same chatroom
# (member_hashID, (name, ip, port, msgID))
USER_MEMBER = {}

# user message ID (starting from 0)
USER_MSGID = 0

# user hash ID
USER_HASHID = 0

# a timer object
KEEPALIVE = KEEPALIVETimerClass()

# a list of all thread handlers
USER_THREAD = []

# a lock object to protect global variables
gLock = threading.Lock()

# a flag variable to control all threads
all_thread_running = True




#
# End of Global variables
#



#
# Other function calls
#

def hash_list():
	# List out global variables
	global USER_MEMBER

	gList = []
	gLock.acquire()
	for hid, info in USER_MEMBER.items():
		print("[hash_list] ", hid)
		gList.append(hid)
	gLock.release()
	return sorted(gList)

def p2p_handshake(hashid, sckt):
	# List out global variables
	global USER_ROOM, USER_NAME, USER_IP, USER_PORT,  USER_MSGID, USER_MEMBER

	sckt.settimeout(3.0)
	# P:roomname:username:IP:Port:msgID::\r\n
	msg = "P:" + USER_ROOM + ":" + USER_NAME + ":" + USER_IP + ":" + USER_PORT + ":" + USER_MSGID + "::\r\n"
	# send message
	sckt.send(msg.encode("ascii"))
	# receive message
	try:
		rmsg = sckt.receive(500)
	# error: No response; peer just close the connection
	except socket.timeout:
		return False
	except socket.error as err:
		print("[p2p_handshake] Receive Error: ", err)
		return False

	rmsg_lst = rmsg.decode("ascii").split(':')
	
	# no error: get S:msgID::\r\n
	if (rmsg_lst[0] != "S"):
		return False
	
	gLock.acquire()
	USER_MEMBER[hashid][3] = rmsg_lst[1]
	gLock.release()

	return True
	


# A funtion for sending out JOIN request
def send_join():
	# List out global variables
	global USER_ROOM, USER_NAME, USER_IP, USER_PORT, USER_SCKT

	# JOIN request -- J:roomname:username:userIP:userPort::\r\n
	join_requ = "J:" + USER_ROOM + ":" + USER_NAME + ":" + USER_IP + ":" + USER_PORT+"::\r\n"
	print(join_requ)
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



def connect_member(sckt):
	# List out global variables
	global USER_HASHID, USER_MEMBER, USER_BSCKT, USER_FSCKT

	# sorted list with member hashID 
	lst = hash_list()

	if len(lst) == 1:
		return False
	
	start = lst.index(USER_HASHID)+1
	
	while (lst[start] != USER_HASHID):
	
		gLock.acquire()
		ip = USER_MEMBER[lst[start]][1]
		port = USER_MEMBER[lst[start]][2]
		
		# if there is a BACKWARD LINK between start and this program
		if lst[start] in USER_BSCKT:
			start = (start+1) % lst.size()
			gLock.release()
			continue
		else:
			# set_connection to lst[start]
			try:
				sckt.connect(ip, int(port))
			except socket.error as serr:
				print("[connect_member] socket connect error: ", serr)
				start = (start+1) % lst.size()
				gLock.release()
				continue

			if p2p_handshake(lst[start], sckt):
				USER_FSCKT[0] = (lst[start], sckt)
				gLock.release()
				CmdWin.insert(1.0, "\nLink to %s" % USER_MEMBER[lst[start]][0] )
				return True
			else:
				start = (start+1) % lst.size()
				gLock.release()
				continue
		
	return False


def text_flooding(sckt, linkType):

	global all_thread_running, USER_MEMBER

	# set blocking duration to 1.0 second
	sckt.settimeout(1.0)

	# start lining
	while all_thread_running:
	
		# wait for any message to arrive
		try:
			rmsg = sckt.recv(500)
		except socket.timeout:
			continue
		except socket.error as err:
			print("[client_thd] Message receiving error at thread %s: %s\n" % (myName, err))
			continue

		# if a message arrived, do the following
		if rmsg:
			CmdWin.insert(1.0,"\nGot a message.")
			
			rmsg_seg = rmsg.decode("ascii").split(':')
			
			# record origin info
			origin_msgType = rmsg_seg[0]
			origin_chatroom = rmsg_seg[1]
			origin_hashID = rmsg_seg[2]
			origin_name = rmsg_seg[3]
			origin_msgID = rmsg_seg[4]
			origin_msgLen = rmsg_seg[5]
			origin_msgCon = rmsg_seg[6]
			
			# check message validity
			if origin_msgType != 'T':
				print("[client_thd] Message flooding error (not a TEXT message) at thread %s: %s\n" % myName)
				continue
			if origin_chatroom != USER_ROOM:
				print("[client_thd] Message flooding error (not the same chatroom) at thread %s: %s\n" % myName)
				continue
			gLock.acquire()
			if origin_msgID < USER_MEMBER[origin_hashID][3]:
				print("[client_thd] Message flooding error (duplicate message) at thread %s: %s\n" % myName)
			gLock.release()
			
			# display the message in the Message Window
			MsgWin.insert(1.0, "[%s] %s" % (origin_name, origin_msgCon))

			# relay the message to other chatroom members
			CmdWin.insert(1.0,"\nRelay the message to other chatroom members.")

			gLock.acquire()
			# backward links
			if len(USER_BSCKT) > 1:
				for hid, each_sckt in USER_BSCKT:
					if each_sckt != sckt:
						each_sckt.send(rmsg)
			# forward link
			for each_sckt in USER_FSCKT:
				each_sckt.send(rmsg)
			gLock.release()

		# else a broken connection is detected, do the following
		else:
			print("[client_thd] The peer connection is broken at thread %s\n" % myName)
			
			# check link type for further action
			
			if linkType == "Forward":
				# remove the forward link from list
				gLock.acquire()
				del USER_FSCKT[0]
				gLock.release()
				
				# search for a new forward link
				index = True
				while index:
					index = not connect_member(sckt)
				
				# continue with the newly establiched forwrd link
				continue
		
			else:
				# remove the backward link from list
				sckt.close()
				gLock.acquire()
				del USER_BSCKT[peer_hashID]
				gLock.release()
				
				break

	# termination
	print("[client_thd] Termination at thread %s\n" % myName)
	return


#
# End of Other function calls
#



#
# Thread handlers
#

def forward_thd():

	fsckt = socket.socket()

	index = True
	while index:
		# build a forward link
		index = connect_member(fsckt)
		if index:
			### Text flooding procedure ###
			text_flooding(fckt, "Forward")
		else:
			continue
	return

def client_thd(csckt, caddr):

	# List out global variables
	global USER_ROOM, USER_MEMBER, USER_MSGID, USER_STATE, USER_BSCKT

	# get name of thread
	myName = threading.currentThread().name
	
	### Handshaking procedure ###
	
	# receive request message
	try:
		rmsg = csckt.recv(500)
	except socket.error as err:
		print("[client_thd] Request message error at thread %s: %s" % (myName, err))
		csckt.close()
		return

	rmsg_seg = rmsg.decode("ascii").split(':')

	# record peer info
	peer_name = rmsg_seg[2]
	peer_ip = rmsg_seg[3]
	peer_port = rmsg_seg[4]
	peer_msgID = rmsg_seg[5]
	peer_hashID = sdbm_hash(peer_name+peer_ip+peer_port)

	# check request message validity
	if (rmsg_seg[0] != 'P') or (rmsg_seg[1] != USER_ROOM):
		print("[client_thd] Handshaking error at thread %s" % myName)
		csckt.close()
		return

	gLock.acquire()
	result = USER_MEMBER.get(peer_hashID, "F")
	gLock.release()
	if result == "F":
		# send a join request to room server for the latest member list
		join_resp_decode = send_join()
		if not (peer_name in join_resp_decode):
			print("[client_thd] %s not in member list, terminating connection at thread %s" % (peer_name, myName))
			csckt.close()
			return

	# send response message
	gLock.acquire()
	smsg = "S:" + USER_MSGID + "::\r\n"
	csckt.send(smsg.encode("ascii"))
	gLock.release()

	# acknowledge successful backward linked connection
	CmdWin.insert(1.0, "\n%s has linked to me" % peer_name)

	# update USER_STATE
	gLock.acquire()
	USER_STATE = "CONNECTED"
	print("At state %s: " % USER_STATE)
	gLock.release()
	
	# add the new client socket to USER_BSCKT
	gLock.acquire()
	USER_BSCKT[peer_hashID] = csckt
	gLock.release()

	### Text flooding procedure ###
	text_flooding(csckt, "Backward")

	return



def listen_thd():
	# List out global variables
	global USER_THREAD, USER_IP, USER_PORT, all_thread_running

	# create a socket for continuous listening
	listen_sckt = socket.socket()
	
	# inform OS not to hold up the port number and allow us restart the listening thread
	listen_sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# set the server listening socket to have a timeout duration of 1.0 second
	listen_sckt.settimeout(1.0)

	try:
		listen_sckt.bind((USER_IP, int(USER_PORT)))
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
		gLock.acquire()
		USER_THREAD.append(cthd)
		gLock.release()

	return


#
# End of Thread handlers
#

#
# Functions to handle user input
#

def do_User():
	
	# List out global variables
	global USER_STATE, USER_NAME

	CmdWin.insert(1.0, "\nPress List")
	
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
	gLock.acquire()
	USER_STATE = "NAMED"
	print("At state %s: " % USER_STATE)
	gLock.release()

	return


def do_List():
	
	# List out global variables
	global USER_SCKT 
	
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
	global USER_STATE, USER_ROOM, KEEPALIVE, USER_THREAD
	
	
	CmdWin.insert(1.0, "\nPress JOIN")
	
	gLock.acquire()
	# user have not yet input username
	if USER_STATE == "START":
		CmdWin.insert(1.0, "\nPlease input your username first")
		userentry.delete(0, END)
		gLock.release()
		return
	# user already joined a chatroom
	if USER_STATE == "JOINED" or USER_STATE == "CONNECTED":
		CmdWin.insert(1.0, "\nYou have already joined a chatroom group: " + USER_ROOM)
		userentry.delete(0, END)
		gLock.release()
		return
	gLock.release()


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
		CmdWin.insert(1.0, "\n"+join_resp_decode[1])
		return

	# room server responds normally
	# M:MSID:userA:A_IP:A_port:userB:B_IP:B_port::\r\n
	elif join_resp_decode[0] == "M":
	
		CmdWin.insert(1.0, "\nSuccessfully joined the chatroom: " + USER_ROOM)
		gLock.acquire()
		USER_STATE = "JOINED"
		print("At state %s: " % USER_STATE)
		gLock.release()
		
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
			room_member += ("\n\t" + str(count) + ": " + name)
			room_member += ("\t" + ip)
			room_member += ("\t" + port)
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
		gLock.acquire()
		USER_THREAD.append(fthd)
		gLock.release()

		# create and start a listening thread
		lthd = threading.Thread(name="listenThread", target=listen_thd)
		lthd.start()

		# add the forward thread to the list of thread handlers
		gLock.acquire()
		USER_THREAD.append(lthd)
		gLock.release()

	return

def do_Send():
	# List out global variables
	global USER_STATE, USER_MSGID, USER_MEMBER, USER_HASHID, USER_ROOM, USER_NAME, USER_FSCKT, USER_BSCKT

	CmdWin.insert(1.0, "\nPress Send")

	
	msg = userentry.get()
	# check if user input is empty
	if msg == "":
		CmdWin.insert(1.0, "\nEmpty message")
		return
	# check if the program has joined or connected to a chatroom program
	gLock.acquire()
	if len(USER_MEMBER) == 1:
		CmdWin.insert(1.0, "\nNo other member in your chatroom. Please wait for others.")
		gLock.release()
		return
	if USER_STATE == "JOINED":
		CmdWin.insert(1.0, "\nYou have not yet connect to a chatroom network. Please try again later.")
		gLock.release()
		return
	if USER_STATE != "CONNECTED":
		CmdWin.insert(1.0, "\nYou have not yet join a chatroom.")
		gLock.release()
		return

	USER_MSGID += 1
	USER_MEMBER[USER_HASHID][3] += 1
	# T:roomname:originHID:origin_username:msgID:msgLength:Message content::\r\n
	message = "T:"+USER_ROOM+":"+USER_HASHID+":"+USER_NAME+":"+USER_MSGID+":"+str(len(msg))+msg+"::\r\n"
	# send to all peers
	# FORWARD LINK
	if (len(USER_FSCKT) != 0):
		# send message
		USER_FSCKT[1].send(message.encode("ascii"))
	# BACKWARD LINK
	for hid, sckt in USER_BSCKT:
		# send message
		sckt.send(message.encode("ascii"))

	gLock.release()

	# display message
	CmdWin.insert(1.0, "\n"+USER_NAME+": "+msg)

	return


def do_Quit():
	# List out global variables
	global USER_STATE, KEEPALIVE, USER_FSCKT, USER_BSCKT, USER_THREAD, all_thread_running

	CmdWin.insert(1.0, "\nPress Quit")
	
	print("Shutdown P2PChat")
	
	# ask all threads to terminate
	all_thread_running = False
	
	# close all sockets
	gLock.acquire()
	for each_sckt in USER_FSCKT:
		each_sckt.close()
	for each_hashID, each_sckt in USER_BSCKT:
		each_sckt.close()
	

	# wait for all threads to terminate
	gLock.acquire()
	for each_thread in USER_THREAD:
		each_thread.join()
	gLock.release()


	print("All threads terminated. Bye!")

	gLock.acquire()
	USER_STATE = "TERMINATED"
	print("At state %s: " % USER_STATE)
	gLock.release()

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
	global USER_SCKT, USER_IP, USER_HASHID, USER_PORT

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

