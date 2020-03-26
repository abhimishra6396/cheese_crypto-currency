from socket import *
from threading import Thread
from util import *
import random
import time

tracker_ip = '192.168.0.46'
tracker_port = 20000
max_member_sample_size = 3

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
						ip = mem.split(':')[0]
						port = int (mem.split(':')[1])
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
				addr = ip + ":" + port
				if addr not in self.membersList:
					self.membersList.append(addr)
					print("Successfully adding the member: ",addr)
				conn.sendall(b"201\r\n")
				
			elif l == getMembersCommand:
				sample = [ self.membersList[i] for i in sorted(random.sample(range(len(self.membersList)), 
						max_member_sample_size if len(self.membersList) > max_member_sample_size else len(self.membersList))) ]
				for s in sample:
					conn.sendall((s+"\r\n").encode('UTF-8'))
				conn.sendall(b"200\r\n")
			else:
				conn.sendall((badCommand+"\r\n").encode('UTF-8'))
			conn.close()
		Thread(target=handle).start()


if __name__ == "__main__":
	t = Tracker()
	t.startListning()
