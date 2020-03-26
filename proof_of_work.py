from member import Member
from random import randint

import time


if __name__ == "__main__":

	member_list = []

	start = time.time()

	for i in range(2):
		member_list.append(Member(i+1, randint(1000, 8999)))
		member_list[i].activateMember()
		member_list[i].startListening()
	member_list[1].shareTransactionDetails("A_B_500")
	member_list[1].shareTransactionDetails("B_C_100")
	member_list[0].shareTransactionDetails("C_A_101")
	member_list[0].shareTransactionDetails("A_B_500")

	#while True:
		#if (time.time()-start > 10):
			#print(member_list[0].cheesestack)
			#print(member_list[1].cheesestack)
			#print(member_list[0].requestTransactionDetails(1))
			#break
