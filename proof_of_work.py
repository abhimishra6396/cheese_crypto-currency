from member import Member
from random import randint


if __name__ == "__main__":

	member_list = [] 

	for i in range(5):
		member_list.append(Member(randint(1000, 8999)))
		member_list[i].activateMember()
		member_list[i].startListening()
	member_list[0].cheesestack.createCheese("D_E_1")
	member_list[1].cheesestack.createCheese("F_G_2")