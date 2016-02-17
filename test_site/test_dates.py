# import datetime

from datetime import datetime
from datetime import timedelta

# --- Formulas basicas de datetime:
today = datetime.today()

# tomorrow = today + 1
print today.toordinal()

print today - timedelta(hours=6)




# today_number = today.toordinal()
# print today_number

# today_from_number = datetime.fromordinal(today_number)
# print today_from_number

# today_pretty = today.strftime('%d-%m-%Y')
# print today_pretty


# # date_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')

# date_object = datetime.strptime('01-01-2016','%d-%m-%Y')
# print date_object.toordinal()


# def valid_csv_date(dateordinal):
#     try:
#         datetime.fromordinal(int(dateordinal))
#         return True
#     except ValueError:
#         return False
# print valid_csv_date(735851)


# def pipeline_grouping(date_ordinal):
# 	date = datetime.fromordinal(date_ordinal)
# 	date_month = date.strftime('%B')
# 	date_year = date.strftime('%Y')
# 	date = datetime.toordinal(date)

# 	today = datetime.today().toordinal()
# 	tomorrow = today + 1

# 	if date == today:
# 		group = 'Today'

# 	elif date == tomorrow:
# 		group = 'Tomorrow'

# 	elif today + 7 >= date:
# 		group = 'This Week'

# 	elif today + 30 >= date:
# 		group = 'This Month'

# 	else:
# 		group = date_month + ' ' + date_year

# 	return group


# target_date = 735978 + 31

# print pipeline_grouping(target_date)

