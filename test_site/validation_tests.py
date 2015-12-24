import re
from datetime import datetime


d_RE = {'username': re.compile(r"^[a-zA-Z0-9_-]{3,20}$"),
		'username_error': 'Invalid Username Syntax',
		
		'password': re.compile(r"^.{3,20}$"),
		'password_error': 'Invalid Password Syntax',
		
		'email': re.compile(r'^[\S]+@[\S]+\.[\S]+$'),
		'email_error': 'Invalid Email Syntax',

		'description': re.compile(r"^.{5,100}$"),
		'description_error': 'Descriotion max lenght is 100 characters and min 5.',

		'frequency': re.compile(r"^[0-9]{1,3}$"),
		'frequency_error': 'Frequency should be an integer with maximum 3 digits',

		'last_event_error':'Last event format must be DD-MM-YYYY',

		'comments': re.compile(r"^.{0,200}$"),
		'comments_error': 'Comments cannot excede 200 characters'
		}


validation_attributes = ['username', 'password', 'description', 'frequency', 'last_event', 'comments']


def valid_date(datestring):
    try:
        datetime.strptime(datestring, '%d-%m-%Y')
        return datetime.strptime(datestring, '%d-%m-%Y').toordinal()
    except ValueError:
        return False



def validate_input(target_attribute, user_input):

	if target_attribute not in validation_attributes:
		return None
	error_key = target_attribute + '_error' 
		
	if target_attribute == 'last_event':
		if valid_date(user_input):
			return None
		else:
			return d_RE[error_key]

	if d_RE[target_attribute].match(user_input):
		return None
	else:
		return d_RE[error_key]



username = "amigabledave"
password = "123"
email = "amigabledave@gmail.com"
description ="desc"
frequency="1"
last_event = "28-03-1987"
comments = "There are some comments"


print validate_input('useame', username)
print validate_input('username', username)
print validate_input('password', password)
print validate_input('email', email)
print validate_input('description', description)
print validate_input('frequency', frequency)
print validate_input('last_event', last_event)
print validate_input('comments', comments)













