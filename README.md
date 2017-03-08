# comp3234

* do_User *

global variables: USER_STATE, USER_NAME
check state: only START can use this button

* do_List *
ask for a list
store the chatroom we join in USER_CHATROOM

* do_Join *
send to server: J:USER_CHATROOM:USER_NAME:.....
get back and interpret the message
(deliverable 2) send to the first "other" member: P:USER_CHATROOM:USERNAME:.....