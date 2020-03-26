from cheeses import Cheese, ReblochonCheese

class CheeseStack:
	Reblochon_Cheese = ReblochonCheese()

	def __init__(self):
		self.stack = [CheeseStack.Reblochon_Cheese]
	
	def createCheese(self, content):
		lastseq = self.stack[-1].seq_num

		if self.stack[-1].seq_num!=0:
			lasthash = self.stack[-1].hash
		else:
			lasthash = self.stack[-1].parent_hash

		cheese = Cheese(content, lastseq + 1, lasthash)
		if self.insertCheese(cheese):
			return cheese
		else:
			return -1

	def insertCheese(self, cheese):
		# make sure hash is valid 
		if cheese.hash != cheese.calculateHash():
			return False
		# hash must pass the difficulty check
		if not cheese.hash.startswith("0" * Cheese.DIFFICULTY):
			return False
		# increment id check
		if cheese.seq_num != self.stack[-1].seq_num + 1:
			return False
		# check chain link is valid
		if self.stack[-1].seq_num!=0:
			if cheese.parent_hash != self.stack[-1].hash:
				return False
		else:
			if cheese.parent_hash != self.stack[-1].parent_hash:
				return False
		self.stack.append(cheese)
		return True

	def getCheeseBySeqNum(self, seq_num):
		return self.stack[seq_num]

	def dropLastCheese(self):
		self.stack.pop()

	def isValid(self):
		parent_hash = CheeseStack.Reblochon_Cheese.parent_hash
		last_seq_num = 0	
		for cheese in self.stack[1:]:
			if cheese.hash != cheese.calculateHash():
				return False
			if cheese.parent_hash != parent_hash:
				return False
			if not cheese.hash.startswith("0" * Cheese.DIFFICULTY):
				return False
			if cheese.seq_num != last_seq_num+1:
				return False
			parent_hash = cheese.hash
			last_seq_num = cheese.seq_num
		return True

	def checkBalance(self, content_received):
		client = content_received.split('_')[0]
		amount = int(content_received.split('_')[2])
		clientBalance = 0
		for b in self.stack[1:]:
			#transfer to the client
			if b.content.split('_')[1] == client:
				clientBalance = clientBalance + int(b.content.split('_')[2])
			#transfer from the client
			if b.content.split('_')[0] == client:
				clientBalance = clientBalance - int(b.content.split('_')[2])

		return amount <= clientBalance

	def __repr__(self):
		rp = "{CheeseStack"
		for b in self.stack:
			rp += " " + str(b)
		return rp + "}"

if __name__ == "__main__":
	c = CheeseStack()
	print(c.createCheese("A_B_500"))
	print(c.createCheese("B_C_100"))
	print(c.createCheese("C_A_101"))

	print(c.checkBalance("A_B_100"))

	print(c)
	c.dropLastCheese()
	print(c)
	print(c.isValid())
