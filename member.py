from cheese_stack import CheeseStack
from cheeses import Cheese, ReblochonCheese

from socket import socket, create_connection, gethostname, gethostbyname_ex

from threading import Thread, Timer
import threading

import util
import pickle
import os
import time

TRACKER_IP = "192.168.0.46"
TRACKER_PORT = 20000

MY_IP = "192.168.0.46"

class Member:
	
	CHAIN_PATH = str(os.path.expanduser("~")) + "/.cheese_stack/"
	os.makedirs(CHAIN_PATH, exist_ok=True)

	def __init__(self, port=1112):
		self.path = Member.CHAIN_PATH + str(port)
		self.port = port
		self.memberList = []
		self.registered = False
		self.cheesestack = self.reloadCheeses() # reloadCheeses from Disk
		self.longest_valid_cheesestack = self.reloadCheeses()

	def runLoops(self):
		self.isLoop = True
		def loop():
			self.register() # register client once
			while True and self.isLoop: 
				Thread(target=self.dumpCheese).start() # dumpCheese every 10 seconds
				Thread(target=self.sniffCheeses).start() # sniff for new blocks every 10 seconds
				time.sleep(30)
		Thread(target=loop).start()
	
	def stopLoops(self):
		self.isLoop = False

	def reloadCheeses(self):
		try:
			return pickle.load(open(self.path, "rb"))
		except:
			return CheeseStack()

	def dumpCheese(self):        
		pickle.dump(self.cheesestack, open(self.path, "wb"))

	def updateLongestCheeseStack(self):
		if self.cheesestack.isValid() and len(self.cheesestack) > len(self.longest_valid_cheesestack):
			self.longest_valid_cheesestack = self.cheesestack

		received_cheese_stack = self.fetchCheeseStack()
		if received_cheese_stack.isValid() and len(received_cheese_stack) > len(self.longest_valid_cheesestack):
			self.longest_valid_cheesestack = received_cheese_stack

	def fetchCheeseStack(self):
		new_cheese_stack = self.cheesestack
		self.fetchMembers()    
		for mem in self.memberList:
			ip, port = mem.split(":")
			try:
				connection = create_connection((ip, port))
				connection.sendall(b"GETCHEESESTACK\r\n")
				print("SENT: GETCHEESESTACK")
				self.memberList = []
				response = util.readLine(connection)
				connection.close()
				if response == "NONE":
					print("RECIEVED: NONE")
					continue
				else:
					cs = pickle.loads(response)
					if len(cs) > len(new_cheese_stack):
						new_cheese_stack = cs

			except Exception as e:
				print("GETCHEESESTACK error: ", e)

		return new_cheese_stack

	def register(self):
		try:
			connection = create_connection((TRACKER_IP, TRACKER_PORT))
			connection.sendall(b'REGISTER\r\n') # TODO: send network ip?
			connection.sendall(bytes(str(self.port) + '\r\n', 'utf-8')) 
			connection.close()
			self.registered = True
		except Exception as e:
			print("cannot register member: ", e)

	def fetchMembers(self):
		try:
			connection = create_connection((TRACKER_IP, TRACKER_PORT))
			connection.sendall(b"GETMEMBERS\r\n")
			print("SENT: GETMEMBERS")
			self.memberList = []
			while True:
				l = util.readLine(connection)
				if l == "200":
					break
				else:
					if (l == MY_IP + ':' + str(self.port)): # ignore self
						continue
					self.memberList.append(l)
			print("RECIEVED MEMBERS: ", self.memberList)

		except Exception as e:
			print("getmembers error: ", e)

	def startListening(self):
		listenerSocket = socket()
		listenerSocket.bind((MY_IP, self.port))
		listenerSocket.listen()
		print("socket is listening", self.port )
		def listenerThread():
			while True:
				connection, addr = listenerSocket.accept()
				print("handle connection", addr)
				Thread(target=self.handleClient, args=(connection,)).start()
		Thread(target=listenerThread).start()

	def handleClient(self, connection):
		l = util.readLine(connection)
		print("RECIEVED: ", l)

		if l == "PING":
			connection.sendall(b"200\r\n")
			print("SENT: OK")
		
		if l == "SENDCheese":
			chsedump = util.readLine(connection)
			chse = pickle.loads(chsedump)
			print("RECIVED Cheese: ", chse)
			if len(self.cheesestack.stack) != chse.seq_num:
				print("SENT: DROP")
				connection.sendall(b"DROP\r\n")
			else:    
				status = self.cheesestack.insertCheese(chse)
				self.updateLongestCheeseStack()
				if status:
					print("SENT: OK")
					connection.sendall(b"OK\r\n")
					self.broadcastCheese(chse.seq_num)
				else:
					print("SENT: INVALID")
					connection.sendall(b"INVALID\r\n")
		
		if l == "GETCheese":
			seq_num = util.readLine(connection)
			seq_num = int(seq_num)
			print("RECIEVED: ", seq_num)
			if len(self.cheesestack.stack) > seq_num:
				chsedump = pickle.dumps(self.cheesestack.stack[seq_num])
				connection.sendall(chsedump)
				connection.sendall(b"\r\n")
				print("SENT Cheese: ", self.cheesestack.stack[seq_num])
			else:
				connection.sendall(b"NONE\r\n")
				print("SENT: NONE")

		connection.close()
		print("connection closed")

	def sniffCheeses(self):
		self.fetchMembers()    
		for mem in self.memberList:
			ip, port = mem.split(":")
			fetchseq = str(len(self.cheesestack.stack))
			try:
				connection = create_connection((ip, port))
				connection.sendall(b'GETCheese\r\n')
				print("SENT: GETCheese")
				connection.sendall(bytes(fetchseq + '\r\n', 'utf-8'))
				print("SENT: ", fetchseq)
				response = util.readLine(connection)
				connection.close()
				if response == "NONE":
					print("RECIEVED: NONE")
					continue
				else:
					chse = pickle.loads(response)
					print("RECIEVED Cheese: ", chse)
					status = self.cheesestack.insertCheese(chse)
					self.updateLongestCheeseStack()
					if status:
						print("cheese added!")
					else:
						print("cheese ignored!")
			except Exception as e:
				print("sniffing error: ", e)

	def broadcastCheese(self, seq_num):
		def broadcasterThread():
			self.fetchMembers()
			chsedump = pickle.dumps(self.cheesestack.stack[seq_num])
			for mem in self.memberList:
				ip, port = mem.split(":")
				try:
					connection = create_connection((ip, port))
					connection.sendall(b'SENDCheese\r\n')
					print("SENT: SENDCheese")
					connection.sendall(chsedump)
					connection.sendall(b"\r\n")
					print("SENT Cheese:", self.cheesestack.stack[seq_num])
					response = util.readLine(connection)
					print("RECIVED: ", response)
					connection.close()
					self.registered = True
				except Exception as e:
					print("broadcast error: ", e)

		Thread(target=broadcasterThread).start()



if __name__ == "__main__":
	from random import randint
	mem = Member(randint(1000, 8999))
	mem.runLoops()
	mem.startListening()
	#mem.cheesestack.createCheese("new cheese 1")
	#mem.cheesestack.createCheese("new cheese 2")
