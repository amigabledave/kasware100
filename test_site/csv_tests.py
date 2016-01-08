import csv
from datetime import datetime

today = datetime.today().toordinal()
# print today

#--------------------------------------------

new_ksu = {'ksu_id': None,
		   'ksu_id_digit': None,
		   'ksu_type': 'kas1',
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
		   'history':None}

kas1 = [new_ksu]



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


ksu_attributes = ['ksu_id',
				  'ksu_id_digit',
				  'ksu_type',
				  'ksu_subtype',
				  'element',
				  'local_tags',
				  'global_tags',
				  'parent_ksu_id',
				  'description',
				  'frequency',
				  'best_day',
				  'best_time',
				  'time_cost',
				  'money_cost',
				  'base_effort_points',
				  'is_critical',
				  'comments',
				  'lastest_exe',
				  'next_exe',
				  'target_exe',
				  'in_mission',
				  'status',
				  'start_date',
				  'end_date',
				  'action_nature',
				  'intenalization_lvl',
				  'kas4_valid_exceptions',
				  'kas3_triger_condition',
				  'bigo_eval_date',
				  'wish_excitement_lvl',
				  'imp_person_name',
				  'history']


basic_attributes = ['ksu_id',
				  'ksu_type',
				  'description',
				  'frequency',
				  'lastest_exe',
				  'status',
				  'imp_person_name']




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


#--- Test Site Import CSV -----------------------------------------


path1 = '/Users/amigabledave/kasware100/csv_files/important_people.csv'


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

# digested_csv = digest_csv(path1)
# print digest_csv(csv_path)

def add_ksus_to_set_from_csv(digested_csv, ksu_set):
	for pseudo_ksu in digested_csv:
		ksu = new_ksu(ksu_set)
		for key, value in pseudo_ksu.iteritems():
			ksu[key] = value
		ksu_set.append(ksu)
	return ksu_set


# print add_ksus_to_set_from_csv(digested_csv,kas1)
# add_ksus_to_set_from_csv(digested_csv,kas1)

#--- Failed writting Attempt -----------------------------------------

path2 ='/Users/amigabledave/kasware100/csv_files/writing_test.csv'

def write_on_csv(csv_path, content):
	target = open(csv_path, 'wb')
	csv_writer = csv.writer(target)
	csv_writer.writerow(content)
	target.close
	return

# write_on_csv(path2, 'probando .... probando')


#--- Test Site Export HTML Text -----------------------------------------

def create_csv_for_html(ksu_set, required_attributes):
	result = ""
	i = 0
	for attribute in required_attributes:
		result += attribute + ',' 
	for ksu in ksu_set:
		result += '<br>'
		for attribute in ksu_attributes:
			result += str(ksu[attribute]) + ','
	return result


# print create_csv_for_html(kas1, basic_attributes)




def developer_Action_Load_Set_CSV(csv_path): #xx
	f = open(csv_path, 'rU')
	f.close
	csv_f = csv.reader(f, dialect=csv.excel_tab)
	attributes = csv_f.next()[0].split(',')
	return attributes
	# for row in csv_f:
	# 	digested_ksu = {}
	# 	i = 0
	# 	raw_ksu = row[0].split(',')
	# 	for attribute in raw_ksu:
	# 		digested_ksu[attributes[i]] = attribute
	# 		i += 1
	# 	ksu_details = digested_ksu
	# 	add_ksu_to_set_from_csv(theory, ksu_details, set_name)		
	# theory.put()
	# return



csv_path = '/Users/amigabledave/kasware100/csv_files/Backup_KAS3.csv'

print developer_Action_Load_Set_CSV(csv_path)

