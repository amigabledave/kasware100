from datetime import datetime

# --- Formulas basicas de datetime:
today = datetime.today()
print today

today_number = today.toordinal()
print today_number

today_from_number = datetime.fromordinal(today_number)
print today_from_number

today_pretty = today.strftime('%d-%m-%Y')
print today_pretty


# date_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')

date_object = datetime.strptime('15-12-2015','%d-%m-%Y')


time_object = datetime.strptime('12:00','%I:%M')

print date_object.toordinal()
print time_object.toordinal()














