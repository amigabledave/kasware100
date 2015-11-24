from datetime import datetime
from operator import itemgetter

# --- Formulas basicas de datetime:
# today = datetime.today().toordinal()
# tomorrow = datetime.fromordinal(today+1)
# print today, tomorrow.strftime('%d-%m-%Y')

user_kba_set = []


def new_ksu_kba():
	ksu_id = 'kba_' + str(len(user_kba_set)+1)
	new_ksu = {'ksu_id': ksu_id,
			   'ksu_type':'Key Base Action',
			   'ksu_subtype': None, 
			   'element': None,
			   'local_tags': None,
			   'global_tags': None,
			   'parent_ksu_id': None,
			   'description': None,
			   'frequency': None,
			   'time_cost': 5,
			   'is_critical': False,
			   'comments': None,
			   'lastest_exe':today, 
			   'status':'Active',
			   'next_exe':None,
			   'important_person_name':None,
			   'exe_history':[['Created',today]]}
	return new_ksu



def add_important_person_to_theory(details):
	kba = new_ksu_kba()
	kba['ksu_subtype'] = 'Important Person'
	kba['element'] = '4. Love & Friendship'
	kba['description'] = 'Contactar a ' + details['important_person_name']
	kba['next_exe'] = kba['lastest_exe']+details['frequency']
	for key, value in details.iteritems():
		kba[key] = value
	user_kba_set.append(kba)
	return 




def todays_mission():
	mission = []
	for e in user_kba_set:
		delay = today - e['next_exe']
		status = e['status']
		if delay >= 0 and status=='Active':
			mission.append([e['description'],delay])
	return sorted(mission, key=itemgetter(1), reverse=True)



def kba_done(user_kba_set, ksu_id, exe_comments):
	ksu = user_kba_set[ksu_id]
	delay = today - ksu['next_exe']
	frequency = ksu['frequency']
	exe_history = ksu['exe_history']
	exe_history.append(['Execution No. '+ str(len(exe_history)),today,delay,exe_comments])
	next_exe = today + frequency
	ksu['next_exe'] = next_exe
	ksu['lastest_exe'] = today
	ksu['exe_history'] = exe_history
	return


#---Testing----------------------------------------------------------------------------------------
# print user_kba_set
# today = 735926 - 30
# add_important_person_to_theory({'important_person_name':'Jimmy', 'frequency':7})
# add_important_person_to_theory({'important_person_name':'Luis', 'frequency':14, 'status':'Active'})
# add_important_person_to_theory({'important_person_name':'Elena', 'frequency':30})

# # print user_kba_set
# print
# today = 735926 
# print todays_mission()
# kba_done(user_kba_set, 0, 'me apendeje')
# print
# print todays_mission()
# print
# # print user_kba_set


