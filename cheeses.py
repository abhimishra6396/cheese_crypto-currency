# TODO: timestamp required?
# self.timestamp.isoformat()

import hashlib
import random

class Cheese:

	DIFFICULTY = 4

	def __init__(self, content, seq_num, parent_hash):
		self.content = content
		self.seq_num = seq_num
		self.parent_hash = parent_hash
		self.updateHash()
	
	def updateHash(self):
		self.nonce = 0
		self.hash = ""
		while not self.hash.startswith("0" * Cheese.DIFFICULTY):
			self.nonce += random.randint(1,1000)
			self.hash = self.calculateHash()

	def calculateHash(self):
		encodedCheese = (
				str(self.content) +
				str(self.seq_num) +
				str(self.nonce) + 
				self.parent_hash).encode('utf-8')
		return hashlib.sha1(encodedCheese).hexdigest()

	def __repr__(self):
		return "<cheese " + str(self.seq_num) + " " + self.content + ">"

class ReblochonCheese:

	def __init__(self):
		self.content = "Öriginal Cheese"
		self.seq_num = 0
		self.parent_hash = ""

	def __repr__(self):
		return "<cheese " + str(self.seq_num) + " " + self.content + ">"	

if __name__ == "__main__":
	c = Cheese("test cheese", 123, "011")
	rc = ReblochonCheese()
	print(c)
	print(rc)
