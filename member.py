from cheese_stack import CheeseStack
from cheeses import Cheese, ReblochonCheese

from socket import socket, create_connection, gethostname, gethostbyname_ex

from threading import Thread, Timer
import threading

import json
import pickle
import os
import time

TRACKER_IP = "192.168.0.46"
TRACKER_PORT = 20000

MY_IP = "192.168.0.46"

class Member:
	
	CHAIN_PATH = str(os.path.expanduser("~")) + "/.cheese_stack/"
	os.makedirs(CHAIN_PATH, exist_ok=True)

	def myReadLine(self, connection):
		readval = b""
		flag = True
		while flag:
			byte = connection.recv(1)
			if byte == b"\n":
				flag = False
			else:
				readval += byte
		return readval

	def __init__(self, member_id, port=1114):
		self.id = member_id
		self.path = Member.CHAIN_PATH + str(port)
		self.port = port
		self.memberList = []
		self.registered = False
		self.cheesestack = self.reloadCheeses()
		self.longest_valid_cheesestack = self.reloadCheeses()

	def activateMember(self):
		def loop():
			self.register()
			while True: 
				Thread(target=self.dumpCheese).start()
				Thread(target=self.sniffCheeses).start()
				time.sleep(300)
		Thread(target=loop).start()

	def reloadCheeses(self):
		try:
			return pickle.load(open(self.path, "rb"))
		except:
			return CheeseStack()

	def dumpCheese(self):        
		pickle.dump(self.cheesestack, open(self.path, "wb"))

	def updateLongestCheeseStack(self):
		if self.cheesestack.isValid() and len(self.cheesestack.stack) > len(self.longest_valid_cheesestack.stack):
			self.longest_valid_cheesestack = self.cheesestack

		received_cheese_stack = self.fetchCheeseStack()
		if received_cheese_stack.isValid() and len(received_cheese_stack.stack) > len(self.longest_valid_cheesestack.stack):
			self.longest_valid_cheesestack = received_cheese_stack

	def fetchCheeseStack(self):
		new_cheese_stack = self.cheesestack
		self.fetchMembers()    
		for mem in self.memberList:
			ip = mem["member_ip"]
			port = mem["member_port"]
			try:
				connection = create_connection((ip, port))
				connection.sendall(b"GETCHEESESTACK\n")
				print("Member ", self.id, " transmitted the request for cheesestack")
				self.memberList = []
				response = self.myReadLine(connection).decode("utf-8")
				connection.close()
				if response == "NONE":
					print(self.id, " got nothing")
					continue
				else:
					cs = pickle.loads(response)
					if len(cs.stack) > len(new_cheese_stack.stack):
						new_cheese_stack = cs

			except Exception as e:
				print("Member ", self.id, " Error in getting CheeseStack: ", e)

		return new_cheese_stack

	def register(self):
		try:
			connection = create_connection((TRACKER_IP, TRACKER_PORT))
			connection.sendall(b'REGISTER\n') # TODO: send network ip?
			connection.sendall(bytes(str(self.port) + '\n', 'utf-8')) 
			connection.close()
			self.registered = True
		except Exception as e:
			print("Error in registering the Member: ", self.id, " ", e)

	def fetchMembers(self):
		try:
			connection = create_connection((TRACKER_IP, TRACKER_PORT))
			connection.sendall(b"GETMEMBERS\n")
			print("Member ", self.id, " transmitted the request for Member List")
			self.memberList = []
			while True:
				l = self.myReadLine(connection).decode("utf-8")
				if l == "200":
					break
				else:
					print("Member ", self.id, " got the Member List in JSON: ", l)
					self.memberList = json.loads(l)

		except Exception as e:
			print("Error in getting the Members by : ", self.id, " ", e)

	def startListening(self):
		listenerSocket = socket()
		listenerSocket.bind((MY_IP, self.port))
		listenerSocket.listen()
		print("Member ", self.id, " is listening on port: ", self.port )
		def listenerThread():
			while True:
				connection, addr = listenerSocket.accept()
				print("Handling the connection by Member: ", self.id, " on Address: ", addr)
				Thread(target=self.handleClient, args=(connection,)).start()
		Thread(target=listenerThread).start()

	def sendTransactionDetails(self, connection):
		seq_num = self.myReadLine(connection).decode("utf-8")
		seq_num = int(seq_num)
		print("Member ", self.id, " received the request for Transaction details with sequence number: ", seq_num)

		chsedump = pickle.dumps(self.cheesestack.stack[seq_num].content)
		connection.sendall(chsedump)
		connection.sendall(b"\n")
		print("Member ", self.id, " transmitted the transaction details: ", self.cheesestack.stack[seq_num].content)

	def sendCheese(self, connection):
		seq_num = self.myReadLine(connection).decode("utf-8")
		seq_num = int(seq_num)
		print("Member ", self.id, " received the request for cheese with sequence number: ", seq_num)
		if len(self.cheesestack.stack) > seq_num:
			chsedump = pickle.dumps(self.cheesestack.stack[seq_num])
			connection.sendall(chsedump)
			connection.sendall(b"\n")
			print("Member ", self.id, " transmitted the cheese: ", self.cheesestack.stack[seq_num])
		else:
			connection.sendall(b"NONE\n")
			print("Member ", self.id, " got invalid Cheese request")

	def getCheese(self, connection):
		chsedump = self.myReadLine(connection).decode("utf-8")
		chse = pickle.loads(chsedump)
		print("Member ", self.id, " received the cheese: ", chse)
		if len(self.cheesestack.stack) != chse.seq_num:
			print("Member ", self.id, " dropped the cheese")
			connection.sendall(b"DROP\n")
		else:    
			status = self.cheesestack.insertCheese(chse)
			self.updateLongestCheeseStack()
			if status:
				print("Member ", self.id, " inserted the received cheese")
				connection.sendall(b"OK\n")
				self.broadcastCheese(chse.seq_num)
			else:
				print("Member ", self.id, " got the invalid cheese")
				connection.sendall(b"INVALID\n")

	def getTransaction(self, connection):
		txndump = self.myReadLine(connection).decode("utf-8")
		txn = pickle.loads(txndump)
		connection.sendall(b"200\n")
		print("Member ", self.id, " received the transaction: ", txn)

		self.cheesestack.createCheese(txn)
		self.broadcastCheese(len(self.cheesestack.stack)-1)

	def sendCheeseStack(self, connection):
		chsestackdump = pickle.dumps(self.cheesestack)
		connection.sendall(chsestackdump)
		connection.sendall(b"\n")
		print("Member ", self.id, " did transmit the CheeseStack: ", self.cheesestack)

	def responseToPing(self, connection):
		print("Member ", self.id, " received the ping request")
		connection.sendall(b"200\n")
		print("Member ", self.id, " responsed to ping")

	def handleClient(self, connection):
		l = self.myReadLine(connection).decode("utf-8")

		if l == "PING":
			self.responseToPing(connection)
		
		if l == "SENDCheese":
			self.getCheese(connection)

		if l == "SENDTrnxn":
			self.getTransaction(connection)
		
		if l == "GETCheese":
			self.sendCheese(connection)

		if l == "GETCHEESESTACK":
			self.sendCheeseStack(connection)

		if l == "GETRXN":
			self.sendTransactionDetails(connection)

		connection.close()

	def getSniffedCheese(self, connection):
		response = self.myReadLine(connection).decode("utf-8")
		connection.close()
		status_sniff = False
		if response == "NONE":
			print("Member ", self.id, " did not receive the cheese that it requested")
			return status_sniff
		else:
			chse = pickle.loads(response)
			print("Member ", self.id, " received the cheese: ", chse)
			status = self.cheesestack.insertCheese(chse)
			self.updateLongestCheeseStack()
			if status:
				print("Member ", self.id, " Added a new cheese")
			else:
				print("Member ", self.id, " Ignored the cheese")
			status_sniff = True
			return status_sniff

	def sniffCheeses(self):
		self.fetchMembers()    
		for mem in self.memberList:
			ip = mem["member_ip"]
			port = mem["member_port"]
			fetchseq = str(len(self.cheesestack.stack))
			try:
				connection = create_connection((ip, port))
				connection.sendall(b'GETCheese\n')
				print("Member ", self.id, " sent the cheese request")
				connection.sendall(bytes(fetchseq + '\n', 'utf-8'))
				print("Member ", self.id, " transmitted the cheese request for sequence number: ", fetchseq)
				if not self.getSniffedCheese(connection):
					continue

			except Exception as e:
				print("sniffing error: ", e)

	def broadcastCheese(self, seq_num):
		def broadcastThread():
			self.fetchMembers()
			chsedump = pickle.dumps(self.cheesestack.stack[seq_num])
			for mem in self.memberList:
				ip = mem["member_ip"]
				port = mem["member_port"]
				try:
					connection = create_connection((ip, port))
					connection.sendall(b'SENDCheese\n')
					print("Member ", self.id, " broadcasted the cheese")
					connection.sendall(chsedump)
					connection.sendall(b"\n")
					print("Transmitted Cheese:", self.cheesestack.stack[seq_num])
					response = self.myReadLine(connection).decode("utf-8")
					print("Member ", self.id, " received the broadcast response: ", response)
					connection.close()
					self.registered = True
				except Exception as e:
					print("Member ", self.id, " had the broadcast error: ", e)

		Thread(target=broadcastThread).start()

	def shareTransactionDetails(self, transaction):
		#def transactionBroadcast():
		self.fetchMembers()
		trxndump = pickle.dumps(transaction)
		for mem in self.memberList:
			ip = mem["member_ip"]
			port = mem["member_port"]
			if port!=str(self.port):
				try:
					connection = create_connection((ip, port))
					connection.sendall(b'SENDTrnxn\n')
					print("Member ", self.id, " broadcasted the Transaction")
					connection.sendall(trxndump)
					connection.sendall(b"\n")
					print("Transmitted transaction:", transaction)
					response = self.myReadLine(connection).decode("utf-8")
					print("Member ", self.id, " received the broadcast transaction response: ", response)
					connection.close()

				except Exception as e:
					print("Member ", self.id, " had the broadcast error: ", e)

		#Thread(target=transactionBroadcast).start()

	def requestTransactionDetails(self, seq_num):
		#def transactionRequestBroadcast():
		self.fetchMembers()
		trnxn = ""
		for mem in self.memberList:
			ip = mem["member_ip"]
			port = mem["member_port"]
			if port!=str(self.port):
				try:
					connection = create_connection((ip, port))
					connection.sendall(b"GETRXN\n")
					connection.sendall(bytes(str(seq_num) + '\n', 'utf-8'))
					#connection.sendall(b"\n")
					print("Member ", self.id, " transmitted the request for transaction details")
					response = self.myReadLine(connection).decode("utf-8")
					connection.close()
					if response == "NONE":
						print(self.id, " got nothing")
						continue
					else:
						trnxn = pickle.loads(response)
						break

				except Exception as e:
					print("Member ", self.id, " Error in getting Transaction details: ", e)

		return trnxn

		#Thread(target=transactionRequestBroadcast).start()
