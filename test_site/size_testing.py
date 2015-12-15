import pickle, random, string




def make_salt(lenght = 5):
    return ''.join(random.choice(string.letters) for x in range(lenght))
	    	


def new_random_to_do():
	to_do = {'ksu_id': make_salt(12),
			 'element': make_salt(8),
			 'status':'Pending', # ['Done', 'Pending', 'Deleted']
			 'description': make_salt(140),
			 'priority_lvl':9,
			 'target_exe':make_salt(10),
			 'in_mission': False,
		     'is_visible': True,
		     'is_critical': False,
			 'done_date':make_salt(10),
			 'effort_points':make_salt(2), # In a fibonacci scale
			 'comments':make_salt(30)} # Passed in as as an optinal parameter
	return to_do




def generate_string(n):
	result = ""
	for i in range(0,n):
		result +="a"
	return result



def generate_random_to_dos(n):
	result = []
	for i in range(0,n):
		to_do = new_random_to_do()
		result.append(to_do)
	return result



test_id = "ksu_1"

def get_digit_from_id(ksu_id):
	return int(ksu_id.split("_")[1])


print get_digit_from_id(test_id)

# test = generate_random_to_dos(2000)

# print test
# print
# print
# print pickle.dumps(test)
# print
# print
# print pickle.loads(pickle.dumps(test))






