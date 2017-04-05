# comp3234 

P2P HANDSHAKE
	send
		P:roomname:username:IP:Port:msgID::\r\n
	receive
		S:msgID::\r\n
		USER_STATE = "CONNECTED"

	receive
		P:roomname:username:IP:Port:msgID::\r\n
	send
		S:msgID::\r\n
		if USER_STATE = "JOINED":
			USER_STATE = "CONNECTED"


MESSAGE FLOODING
	receive message T:roomname:originHID:origin_username:msgID:msgLength:Message content::\r\n
		if not recognize originHID:
			ask the server
			update USER_MEMBER
		else:
			if duplicate:
				do nothing
			else:
				update msgID of originHID
				send to all members

FORWARD LINK
	check forward link periodically
	if broken, connect_member()
		if succeed: USER_STATE = "CONNECTED"
		
		
CLIENT_THD
	text flooding
		need to add the procedure of checking msgID



