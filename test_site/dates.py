from datetime import datetime

# # --- Formulas basicas de datetime:
# today = datetime.today()
# print today

# today_number = today.toordinal()
# print today_number

# today_from_number = datetime.fromordinal(today_number)
# print today_from_number

# today_pretty = today.strftime('%d-%m-%Y')
# print today_pretty


# # date_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')

# date_object = datetime.strptime('01-01-2016','%d-%m-%Y')
# print date_object.toordinal()







def valid_csv_date(dateordinal):
    try:
        datetime.fromordinal(int(dateordinal))
        return True
    except ValueError:
        return False


print valid_csv_date(735851)







