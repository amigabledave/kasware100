import pickle, random, string




def ksu_template():
	template = {'ksu_id': None,	
				'ksu_subtype':None,			
		    	'element': None,
		    	'description': None,
		    	'comments': None,
		    	'local_tags': None,
		    	'global_tags': None,
		    	'parent_ksu_id': None,
		    	'priority_lvl':9,
		    	'is_critical': False,
		    	'is_visible': True,
		    	'is_private': False}
	return template	



def create_ksu_id(ksu_set):
	ksu_type = ksu_set[0]['ksu_type']
	id_digit = ksu_set[0]['set_size']
	ksu_set[0]['set_size'] = int(id_digit) + 1
	ksu_id = ksu_type + '_'+ str(id_digit)
	return ksu_id


def new_ksu_in_kas1(kas1):
	ksu = ksu_template()
	ksu_id = create_ksu_id(kas1)
	ksu['ksu_id'] = ksu_id
	ksu['status'] = 'Active' # ['Active', 'Hold', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['frequency'] = None
	ksu['best_day'] = None
	ksu['best_time'] = None
	ksu['lastest_exe'] = None
	ksu['next_exe'] = None
	ksu['target_exe'] = None
	return ksu



def new_ksu_in_kas2(kas2):
	ksu = ksu_template()
	ksu_id = create_ksu_id(kas2)
	ksu['ksu_id'] = ksu_id
	ksu['status'] = 'Pending' # ['Done', 'Pending', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['best_time'] = None
	ksu['target_exe'] = None
	return ksu




def new_event():
	event = {'type':None, # [Created, Edited ,Deleted, Happiness, Effort]
			 'ksu_id': None,
			 'element': None, # This is only here because KAS2 skus will be deleted
			 'description': None, # Passed in as as an optional parameter
			 'date':today,
			 'duration':0, #To record duration of happy moments
			 'points':0} # In a fibonacci scale
	return event


def record_event(theory, event):
	return






# --- Old KSU Template ---

def ksu_template():
	template = {'ksu_id': None,
				'ksu_id_digit': None,
		   		'ksu_type': None,
		   		'ksu_subtype': None, 
		    	'element': None,
		    	'local_tags': None,
		    	'global_tags': None,
		    	'parent_ksu_id': None,
		    	'description': None,
		    	'frequency': None,
		    	'best_day':None,
		    	'best_time':None,
		    	'time_cost': 0,
		    	'money_cost':0,
		    	'base_effort_points':0,
		    	'priority_lvl':9,
		    	'is_critical': False,
		    	'comments': None,
		    	'lastest_exe':None, 
		    	'next_exe':None,
		    	'target_exe':None,
		    	'in_mission': False,
		    	'is_visible': True,
		    	'is_private': False,
		    	'status':'Active',
		    	'start_date':None,
		    	'end_date':None,
		    	'action_nature':None, # Enjoy or Produce
		    	'internalization_lvl':None,
		    	'kas4_valid_exceptions':None,
		    	'kas3_triger_condition': None,
		    	'bigo_eval_date':None,
		    	'bigo_type':None, # End Goal or Sprint Goal
		    	'wish_excitement_lvl':None,
		    	'imp_person_name':None,
		    	'history':None}
	return template		    	




#--- Old event functions




def new_event():
	event = {'event_date':today,
			 'event_type':None, # [Created, Edited ,Deleted, Happiness, Effort]
			 'event_duration':0, # In minutes rounded down
			 'event_value':0, # In a fibonacci scale
			 'event_comments':None} # Passed in as as an optinal parameter
	return event




def add_effort_event_to_ksu(ksu, post_details):
	event = new_event()
	event['event_type'] = 'Effort'
	event['event_comments'] = post_details['event_comments']
	event['event_duration'] = post_details['event_duration']
	event_points['event_value'] = ksu['base_effort_points']
	history = ksu['history']
	history.append(event)
	ksu['history'] = history
	return

def effort_event(post_details):
	event = new_event()
	event['event_type'] = 'Effort'
	event['event_comments'] = post_details['event_comments']
	event['event_duration'] = post_details['event_duration']
	event['event_value'] = post_details['event_value']
	return event


def happiness_event(post_details):
	event = new_event()
	event['event_type'] = 'Happiness'
	event['event_comments'] = post_details['event_comments']
	event['event_duration'] = post_details['event_duration']
	event['event_value'] = int(post_details['event_duration']) * int(post_details['event_base_intensity']) + int(post_details['event_spike_intensity'])
	return event


def add_event_to_ksu(ksu, event):
	history = ksu['history']
	history.append(event)
	ksu['history'] = history
	return






#--- Size testing -------------------------------------------------------------------------------------------------



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






