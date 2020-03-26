from socket import *
from threading import Thread

import json

from util import *
import random
import time

tracker_ip = '192.168.0.46'
tracker_port = 20000

class Tracker:

	def __init__(self):
		self.membersList = []

	def startListning(self):
		def acceptAll():
			serverSocket = socket()
			serverSocket.bind((tracker_ip,tracker_port))
			serverSocket.listen()
			while True:
				conn, addr = serverSocket.accept()
				self.handleClient(conn, addr[0])
		
		def pingAll():
			while True:
				print("Pinging all members")
				for mem in self.membersList:
					try:
						ip = mem["member_ip"]
						port = mem["member_port"]
						print("Starting ping member:",ip,port)
						conn = create_connection((ip,port))
						conn.sendall(b"PING\r\n")
						l = readLine(conn)
						if l != "200":
							print("Pinging the Member:",ip,port," with response: ",l)
						else:
							print("Pinging the Member:",ip,port," with response: ",l)
					except:
						print("Pinging the Member:",ip,port," Member timeout, Now deleting the Member!")
						self.membersList.remove(mem)
				time.sleep(60)

		Thread(target=pingAll).start()
		Thread(target=acceptAll).start()
	
	def handleClient(self,conn, ip):
		def handle():
			
			l = readLine(conn)
			#print(l)
			if l == addMemberCommand:
				port = readLine(conn)
				addr = {}
				addr["member_ip"]= ip
				addr["member_port"] = port
				if addr not in self.membersList:
					self.membersList.append(addr)
					print("Successfully adding the member: ",addr)
				conn.sendall(b"201\r\n")
				
			elif l == getMembersCommand:
				conn.sendall((json.dumps(self.membersList)+"\r\n").encode('UTF-8'))
				conn.sendall(b"200\r\n")
			else:
				conn.sendall((badCommand+"\r\n").encode('UTF-8'))
			conn.close()
		Thread(target=handle).start()


if __name__ == "__main__":
	t = Tracker()
	t.startListning()
