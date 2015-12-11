from datetime import datetime

# --- Formulas basicas de datetime:
# today = datetime.today()
# print today

# today_number = today.toordinal()
# print today_number

# today_from_number = datetime.fromordinal(today_number)
# print today_from_number

# today_pretty = today.strftime('%d-%m-%Y')
# print today_pretty



def new_master_log(start_date=735942, end_date=736680):
	result = {}
	for date in range(start_date, end_date):
		entry = {'date':0,'Efort':0,'Happiness':0}
		entry['date'] = datetime.fromordinal(date).strftime('%d-%m-%Y')
		result[date] = entry
	return result




test_log = new_master_log(735942,736680)
print test_log











