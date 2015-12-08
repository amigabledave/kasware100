import csv
from datetime import datetime

today = datetime.today().toordinal()
# print today


csv_path = '/Users/amigabledave/kasware100/csv_files/important_people.csv'


#--------------------------------------------

kas1 = [{'ksu_type': 'kas1', 'ksu_subtype': None, 'next_exe':None, 'imp_person_name':None}]

def new_ksu(ksu_set):
	ksu_type = ksu_set[0]['ksu_type']
	id_digit = len(ksu_set)
	ksu_id = ksu_type + '_'+ str(id_digit)
	event = new_event()
	event['event_type'] = 'Created'
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
			   'best_time':None,
			   'time_cost': 0,
			   'money_cost':0,
			   'base_effort_points':0,
			   'is_critical': False,
			   'comments': None,
			   'lastest_exe':None, 
			   'next_exe':None,
			   'target_exe':None,
			   'in_mission': False,
			   'status':'Active',
			   'start_date':None,
			   'end_date':None,
			   'action_nature':None, # Enjoy or Produce
			   'intenalization_lvl':None,
			   'kas4_valid_exceptions':None,
			   'kas3_triger_condition': None,
			   'bigo_eval_date':None,
			   'wish_excitement_lvl':None,
			   'imp_person_name':None,
			   'history':[event]}
	return new_ksu


def new_event():
	event = {'event_date':today,
			 'event_type':None,
			 'event_title':None,
			 'event_people':[],
			 'event_comments':None,
			 'event_duration':0, # In Kasware Time ( 1 unit of Kasware time = 5 minutes. Total time should always be rounded down)
			 'event_intensity':0, # In a fibonacci scale
			 'event_points':0}
	return event


#--------------------------------------------

def digest_csv(csv_path):
	f = open(csv_path, 'rU')
	f.close
	csv_f = csv.reader(f, dialect=csv.excel_tab)
	result = []
	attributes = csv_f.next()[0].split(',')
	for row in csv_f:
		digested_ksu = {}
		i = 0
		raw_ksu = row[0].split(',')
		for attribute in raw_ksu:
			digested_ksu[attributes[i]] = attribute
			i += 1
		result.append(digested_ksu)
	return result

digested_csv = digest_csv(csv_path)
# print digest_csv(csv_path)

def add_ksus_to_set_from_csv(digested_csv, ksu_set):
	for pseudo_ksu in digested_csv:
		ksu = new_ksu(ksu_set)
		for key, value in pseudo_ksu.iteritems():
			ksu[key] = value
		ksu_set.append(ksu)
	return ksu_set


print add_ksus_to_set_from_csv(digested_csv,kas1)





