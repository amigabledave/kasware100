#----------- main.py formulas ----------
import theory, time
import re, os, logging, hashlib, random, string, csv, pickle
from datetime import datetime, timedelta
from operator import itemgetter
from test_import import sample_theory
# print sample_theory.Hist

# from test_import import awesomeness
# awesomeness.awesome_things()


today = datetime.today().toordinal()
# tomorrow = today + 1
# not_ugly_today = datetime.today().strftime('%d-%m-%Y')




i_BASE_Event = {'id':None,
				'ksu_id':None,
				'date':(datetime.today().toordinal() - random.randrange(0, 365)), # asi los eventos pudieron haber sucedido en cualquier momento en el ultimo ano,
				'type':None} # Created, Edited, Deleted, EndValue, SmartEffort or Stupidity


i_Created_Event = {'type':'Created'}

i_Edited_Event = {'type':'Edited',
				  'changes':None}

i_Deleted_Event = {'type':'Deleted',
				   'reason':None}



i_Score_Event = {'value':None, # Points Earned
				 'importance':None} 


i_EndValue_Event = {'type':'EndValue',
					'duration':None, # To calculate Amount of SmartEffort Points Earned
					'effort':False}


i_SmartEffort_Event = {'type':'SmartEffort',
					   'duration':None, # To calculate Amount of SmartEffort Points Earned
					   'repetitions':'1',
			    	   'joy':False,
			    	   'disconfort':False,
			    	   'streak':None}



i_Stupidity_Event = {'type':'Stupidity',
					 'repetitions':'1',
					 'streak':None}



i_Achievement_Event = {'type':'Achievement',
					   'value':None,
					   'target_date':None,
					   'comments':None,
					   'met_expectations':False}





template_recipies = {
					 'Created_Event':[i_BASE_Event, i_Created_Event],
					 'Edited_Event':[i_BASE_Event, i_Edited_Event],
					 'Deleted_Event':[i_BASE_Event, i_Deleted_Event],

					'EndValue_Event':[i_BASE_Event, i_Score_Event, i_EndValue_Event],
					 'SmartEffort_Event':[i_BASE_Event, i_Score_Event, i_SmartEffort_Event],
					 'Stupidity_Event':[i_BASE_Event, i_Score_Event, i_Stupidity_Event],
					 'Achievement_Event':[i_BASE_Event, i_Achievement_Event]}



def make_event_template(event_type):
	template = {}
	target_template = event_type + '_Event'
	template_recipe = template_recipies[target_template]
	for ingredient in template_recipe:
		for (attribute,value) in ingredient.items():
			template[attribute] = value
	return template


def new_set_Hist():
	result = {}
	event = make_event_template('Created')
	event['id'] = 'Event_0'
	event['set_type'] = 'Event'
	event['set_size'] = 0
	result['set_details'] = event
	return pack_set(result)


def new_event(Hist, event_type):
	event = make_event_template(event_type)
	event_id = create_id(Hist)
	event['id'] = event_id
	return event


def create_id(ksu_set):
	set_details = ksu_set['set_details']
	set_type = set_details['set_type']
	id_digit = int(set_details['set_size']) + 1
	set_details['set_size'] = id_digit
	ksu_id = set_type + '_' + str(id_digit)
	return ksu_id


def pack_set(ksu_set):
	return pickle.dumps(ksu_set)


def unpack_set(ksu_pickled_set):
	return pickle.loads(ksu_pickled_set)



def update_set(ksu_set, ksu):
	ksu_id = ksu['id']
	ksu_set[ksu_id]=ksu
	return


def get_type_from_id(ksu_id):
	return ksu_id.split("_")[0]



def create_mega_set(): #The original takes theory as an input argument
	mega_set = {}
	result = {}

	KAS1 = unpack_set(theory.KAS1)
	KAS2 = unpack_set(theory.KAS2)
	KAS3 = unpack_set(theory.KAS3)
	KAS4 = unpack_set(theory.KAS4)
	BigO = unpack_set(theory.BigO)
	BOKA = unpack_set(theory.BOKA)
	
	all_ksu_sets = [KAS1, KAS2, KAS3, KAS4, BigO, BOKA]
	
	for ksu_set in all_ksu_sets:
		mega_set.update(ksu_set)

	for (ksu_id,ksu) in list(mega_set.items()):
		if ksu['is_visible']:
			result[ksu_id] = ksu

	return result


# print create_mega_set().keys()

all_ids = create_mega_set().keys()



def add_EndValue_event(Hist, post_details): # The original takes theory instead of  Hist
	# Hist = unpack_set(Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'EndValue')

	if 'effort' in post_details:
		event['effort'] = True

	event['ksu_id'] = ksu_id
	event['duration'] = post_details['duration']
	event['importance'] = post_details['importance']	
	
	# update_set(Hist, event)
	# update_MLog(theory, event)
	# theory.Hist = pack_set(Hist)
	return event



def add_SmartEffort_event(Hist, post_details): # The original takes theory instead of  Hist
	# Hist = unpack_set(Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'SmartEffort') 
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	poractive_sets = ['KAS1', 'KAS2', 'BOKA']
	reactive_sets = ['KAS3', 'KAS4']
	
	event['ksu_id'] = ksu_id
	event['duration'] = post_details['duration']

	if set_name in poractive_sets:		 
		event['importance'] = post_details['importance']
		if 'joy' in post_details:
			event['joy'] = True
		if 'disconfort' in post_details:
			event['disconfort'] = True

	if set_name in reactive_sets:
		event['importance'] = ksu['importance']
		event['streak'] = ksu['streak']

	event['repetitions'] = post_details['repetitions']	
		
	update_set(Hist, event)
	# update_MLog(theory, event)
	# theory.Hist = pack_set(Hist)
	return event


def add_Stupidity_event(Hist, post_details): # The original takes theory instead of  Hist
	# Hist = unpack_set(Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'Stupidity')
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]

	event['ksu_id'] = ksu_id
	event['importance'] = ksu['importance']
	event['streak'] = ksu['streak']
	event['repetitions'] = post_details['repetitions']
	
	# update_set(Hist, event)
	# update_MLog(theory, event)
	# theory.Hist = pack_set(Hist)	
	return event





def add_Achievement_event(Hist, post_details): # The original takes theory instead of  Hist
	# Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'Achievement') 
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]

	event['ksu_id'] = ksu_id

	event['value'] = post_details['Achievement_Value']
	event['target_date'] = ksu['target_date']
	event['comments'] = post_details['comments']

	if 'met_expectations' in post_details:
		event['met_expectations'] = True
	
	# update_set(Hist, event)
	# update_MLog(theory, event)
	# theory.Hist = pack_set(Hist)

	return event




def calculate_event_score(event):
	result = {'EndValue':0,'SmartEffort':0, 'Stupidity':0, 'Achievement':0}

	poractive_sets = ['KAS1', 'KAS2', 'BOKA']
	reactive_sets = ['KAS3', 'KAS4']
	set_name = get_type_from_id(event['ksu_id'])
	event_type = event['type']

	if event_type == 'EndValue':
		result['EndValue'] = event['value'] = int(event['duration']) * int(event['importance'])
		result['SmartEffort'] = 20 * event['effort']

	elif event_type == 'SmartEffort':

		if set_name in poractive_sets:		
			result['SmartEffort'] = int(event['duration'])*(int(event['importance']) + event['disconfort']) 
			result['EndValue'] = int(event['duration'])*event['joy']
			
		if set_name in reactive_sets: 
			if int(event['importance']) < int(event['streak']):
				result['SmartEffort'] = int(event['importance']) * 2
			else:
				result['SmartEffort'] = int(event['importance']) + int(event['streak'])

	elif event_type == 'Stupidity':

		if int(event['importance']) < int(event['streak']):
			result['Stupidity'] = int(event['importance']) * int(event['repetitions']) + int(event['importance'])
		else:
			result['Stupidity'] = int(event['importance']) * int(event['repetitions']) + int(event['streak'])

	elif event_type == 'Achievement':
		result['Achievement'] = int(event['value'])
	
	return result




#----------- Tests Start Here ---------- 

# print make_event_template('EndValue')
# print
# print make_event_template('SmartEffort')
# print
# print make_event_template('Stupidity')
# print
# print make_event_template('Achievement')

# Hist = new_set_Hist()
# print unpack_set(Hist)

# print create_mega_set().keys()


random_post_details = {'ksu_id':random.choice(all_ids),
					  'duration':random.randrange(5, 120),
					  'repetitions':random.randrange(1, 5),
					  'importance':random.randrange(1, 13),
					  'Achievement_Value':random.randrange(1, 13),
					  'effort':random.choice([None, 'on']), # whe true is 'on'
					  'joy':random.choice([None, 'on']),
					  'disconfort':random.choice([None, 'on']),
					  'met_expectations':random.choice([None, 'on']),
					  'comments':random.choice([None, 'Some random comments'])}
# print random_post_details


# random.choice([add_EndValue_event(Hist, post_details), add_SmartEffort_event(Hist, post_details), add_Stupidity_event(Hist, post_details), add_Achievement_event(Hist, post_details)])


# def generate_dandom_Hisz



def generate_random_Hist_size_n(n):
	Hist = unpack_set(theory.Hist)
	mega_set = create_mega_set()

	for i in range(0, n):

		post_details = {'ksu_id':random.choice(all_ids),
					  'duration':str(random.randrange(5, 120)),
					  'repetitions':str(random.randrange(1, 5)),
					  'importance':str(random.randrange(1, 13)),
					  'Achievement_Value':str(random.randrange(1, 13)), 
					  'effort':random.choice([None, 'on']), # whe true is 'on'
					  'joy':random.choice([None, 'on']),
					  'disconfort':random.choice([None, 'on']),
					  'met_expectations':random.choice([None, 'on']),
					  'comments':random.choice([None, 'Some random comments'])}


		ksu_id = post_details['ksu_id']
		ksu_type = get_type_from_id(ksu_id)
		ksu = mega_set[ksu_id]

		if ksu_type == 'BOKA':
			ksu['value_type'] = None


		ksu_value_type = ksu['value_type']
		if ksu_value_type == 'V000':
			event = random.choice([add_EndValue_event(Hist, post_details)])

		else:			
			if ksu_type == 'KAS1' or ksu_type == 'KAS2' or ksu_type == 'BOKA':
				event = random.choice([add_SmartEffort_event(Hist, post_details)])
				
			elif ksu_type == 'KAS3' or ksu_type == 'KAS4':
				event =random.choice([add_SmartEffort_event(Hist, post_details), add_Stupidity_event(Hist, post_details)])
				
			elif ksu_type == 'BigO':
				event =random.choice([add_Achievement_event(Hist, post_details)])
			
		event['date'] = (datetime.today().toordinal() - random.randrange(0, 365))
		Hist[event['id']] = event
	
	return Hist
print generate_random_Hist_size_n(2000) #xx



def prepare_relevant_history(period_end, period_duration):
	result = {'Score_history':{},'Awesomeness_history':{}, 'AcumulatedPerception_history':{},'RealitySnapshot_history':{}, 'Behaviour_history':{}}
	
	Hist = unpack_set(theory.Hist)
	mega_set = create_mega_set()

	relevant_event_types = ['EndValue', 'SmartEffort', 'Stupidity', 'Achievement']
	score_subtypes = ['EndValue', 'SmartEffort', 'Stupidity', 'Achievement']
	period_start = int(period_end) - int(period_duration)

	for (Event_id, Event) in list(Hist.items()):
		Event_type = Event['type']
		Event_date = int(Event['date'])

		if Event_type in relevant_event_types and Event_date >= period_start and Event_date <= period_end:		
			
			if Event_type in score_subtypes:
				Event['score'] = calculate_event_score(Event)
				ksu_id = Event['ksu_id']
				ksu = mega_set[ksu_id]

				ksu_type = get_type_from_id(ksu_id)	
				if ksu_type == 'BOKA':
					ksu = mega_set[ksu['parent_id']]
				
				Event['target_value_type'] = ksu['value_type']
				Score_history = result['Score_history']
				Score_history[Event_id] = Event

	return result
# print prepare_relevant_history(period_end, period_duration)




indicators_id_list = ['ImIn_1', 'ImIn_2', 'ImIn_3', 'ImIn_4', 'ImIn_5', 'ImIn_6', 'ImIn_7', 'ImIn_8', 'ImIn_9', 'ImIn_38', 'ImIn_55', 'ImIn_53', 'ImIn_24', 'ImIn_76', 'ImIn_81', 'ImIn_80', 'ImIn_82', 'ImIn_58', 'ImIn_67', 'ImIn_51', 'ImIn_57', 'ImIn_40', 'ImIn_59', 'ImIn_39', 'ImIn_65', 'ImIn_25', 'ImIn_41', 'ImIn_66', 'ImIn_43', 'ImIn_64', 'ImIn_63', 'ImIn_62', 'ImIn_61', 'ImIn_60', 'ImIn_49', 'ImIn_22', 'ImIn_21', 'ImIn_20', 'ImIn_27', 'ImIn_26', 'ImIn_69', 'ImIn_68', 'ImIn_47', 'ImIn_46', 'ImIn_42', 'ImIn_45', 'ImIn_50', 'ImIn_23', 'set_details', 'ImIn_28', 'ImIn_48', 'ImIn_56', 'ImIn_54', 'ImIn_52', 'ImIn_12', 'ImIn_13', 'ImIn_10', 'ImIn_11', 'ImIn_16', 'ImIn_17', 'ImIn_14', 'ImIn_15', 'ImIn_34', 'ImIn_18', 'ImIn_19', 'ImIn_44', 'ImIn_35', 'ImIn_74', 'ImIn_75', 'ImIn_29', 'ImIn_77', 'ImIn_70', 'ImIn_71', 'ImIn_72', 'ImIn_73', 'ImIn_30', 'ImIn_31', 'ImIn_32', 'ImIn_33', 'ImIn_78', 'ImIn_79', 'ImIn_36', 'ImIn_37']
# print unpack_set(theory.ImIn).keys()

l_values_types = ['V000', 'V100', 'V200', 'V300', 'V400', 'V500', 'V600', 'V700', 'V800', 'V900']


def make_results_holder():
	result = {}
	for value_type in l_values_types:
		result[value_type] = {'EndValue':0, 'SmartEffort':0, 'Stupidity':0, 'Achievement':0, 'duration':0}
	result['Total'] = {'EndValue':0, 'SmartEffort':0, 'Stupidity':0, 'Achievement':0, 'duration':0}
	return result



def ImIn_calculate_indicators_values(period_end, period_duration):
	results_holder = make_results_holder()
	ImIn = unpack_set(theory.ImIn)
	relevant_history = prepare_relevant_history(period_end, period_duration)
	score_history = relevant_history['Score_history']
	score_units = ['EndValue','SmartEffort','Stupidity','Achievement']

	for event in score_history:
		event = score_history[event]
		score = event['score']

		event_type = event['type']
		if event_type == 'Stupidity' or event_type == 'Achievement':
			duration = 0
		else:
			duration = event['duration'] #xx
		
		target_value_type = event['target_value_type']
		target_holder =	results_holder[target_value_type]
		
		for unit in score_units:
			target_holder[unit] += score[unit]
		target_holder['duration'] += int(duration)

	target_holder = results_holder['Total']

	for value_type in l_values_types:
		score = results_holder[value_type]
		for unit in score_units:
			target_holder[unit] += score[unit]
			target_holder['duration'] += score['duration']

	return results_holder


period_end = str(today)
period_duration = '180'
# print ImIn_calculate_indicators_values(period_end,period_duration)

























