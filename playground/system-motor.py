from datetime import datetime
from operator import itemgetter

# --- Formulas basicas de datetime:
# today = datetime.today().toordinal()
# tomorrow = datetime.fromordinal(today+1)
# print today, tomorrow.strftime('%d-%m-%Y')

ksu_set = [{'ksu_type': 'test_type', 'next_exe':None}]


def pack_set(ksu_set):
	return str(ksu_set)

def unpack_set(ksu_set):
	return eval(ksu_set)



def new_ksu(ksu_set):
	ksu_type = ksu_set[0]['ksu_type']
	id_digit = len(ksu_set)
	ksu_id = ksu_type + '_'+ str(id_digit)
	new_ksu = {'ksu_id': ksu_id,
			   'ksu_id_digit': id_digit,
			   'ksu_type': ksu_type,
			   'ksu_subtype': None, 
			   'element': None,
			   'local_tags': None,
			   'global_tags': None,
			   'parent_ksu_id': None,
			   'description': None,
			   'frequency': None,
			   'best_day':None,
			   'time_cost': 1,
			   'money_cost':0,
			   'is_critical': False,
			   'comments': None,
			   'lastest_exe':None, 
			   'next_exe':None,
			   'target_exe':None,
			   'status':'Active',
			   'start_date':None,
			   'end_date':None,
			   'x_valid_exceptions':None,
			   'x_triger_condition': None,
			   'x_eval_date':None,
			   'x_excitement_lvl':None,
			   'x_person_name':None,
			   'history':[['Created',today,None,None]]} #History Format= [<Event description>, <Event date>, <Event Value>, <Event comments>]

	return new_ksu


def add_important_person_to_theory(details):
	ksu = new_ksu(ksu_set)
	ksu['ksu_subtype'] = 'Important_Person'
	ksu['element'] = '4_Love_Friendship'
	ksu['description'] = 'Contactar a ' + details['x_person_name']
	ksu['next_exe'] = today + details['frequency']
	for key, value in details.iteritems():
		ksu[key] = value
	ksu_set.append(ksu)
	return 


def todays_mission():
	mission = []
	for e in ksu_set:
		if e['next_exe']:
			delay = today - e['next_exe']
			status = e['status']
			if delay >= 0 and status=='Active':
				mission.append([e['description'],delay])
	return sorted(mission, key=itemgetter(1), reverse=True)



def done(ksu_set, ksu_id_digit, event_comments=None):
	ksu = ksu_set[ksu_id_digit]
	event_description = 'Done'
	event_date = today
	event_value = today - ksu['next_exe']
	frequency = ksu['frequency']
	history = ksu['history']
	history.append([event_description, event_date, event_value, event_comments])
	next_exe = today + frequency
	ksu['next_exe'] = next_exe
	ksu['lastest_exe'] = today
	ksu['history'] = history
	return

#KSU History Format= [<Event description>, <Event date>, <KPI Value>, <Event comments>]



#---Testing----------------------------------------------------------------------------------------
# print ksu_set
# today = 735926 - 30
# add_important_person_to_theory({'x_person_name':'Jimmy', 'frequency':7})
# add_important_person_to_theory({'x_person_name':'Luis', 'frequency':14, 'status':'Active'})
# add_important_person_to_theory({'x_person_name':'Dani', 'frequency':30})

# #print ksu_set
# print
# today = 735926 
# print todays_mission()
# done(ksu_set, 1, 'me apendeje feo')
# # print
# print todays_mission()
# print
# print ksu_set


