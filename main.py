#KASware v1.0.0 | Copyright 2015 AmigableDave & Co.

import re, os, webapp2, jinja2, logging, hashlib, random, string, csv
from datetime import datetime, timedelta
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import mail


template_dir = os.path.join(os.path.dirname(__file__), 'html_templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)




# --- Handlers -------------------------------------------------------------------------------------------


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_html(self, template, **kw):
		t = jinja_env.get_template(template)
		if self.theory:
			theory = self.theory
			todays_effort = eval(theory.master_log)[today]['Effort']
			return t.render(theory=theory, todays_effort=todays_effort, **kw)
		else:
			return t.render(**kw)

	def print_html(self, template, **kw):
		self.write(self.render_html(template, **kw))

	def set_secure_cookie(self, cookie_name, cookie_value):
		cookie_secure_value = make_secure_val(cookie_value)
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (cookie_name, cookie_secure_value))

	def read_secure_cookie(self, cookie_name):
		cookie_secure_val = self.request.cookies.get(cookie_name)
		return cookie_secure_val and check_secure_val(cookie_secure_val)

	def login(self, theory):
		self.set_secure_cookie('theory_id', str(theory.key().id()))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'theory_id=; Path=/')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		theory_id = self.read_secure_cookie('theory_id')
		self.theory = theory_id and Theory.get_by_theory_id(int(theory_id)) #if the user exist, 'self.theory' will store the actual theory object




class Home(Handler):
    def get(self):
        self.print_html('home.html')



class Signup(Handler):

	def get(self):
		self.print_html("signup-form.html")

	def post(self):
		have_error = False
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')
		
		params = dict(username = username, email = email)

		if not valid_username(username):
			params['error_username'] = "That's not a valid username."
			have_error = True

		if not valid_password(password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True
		elif password != verify:
			params['error_verify'] = "Your passwords didn't match."
			have_error = True

		if not valid_email(email):
			params['error_email'] = "That's not a valid email."
			have_error = True

		if have_error:
			self.print_html('signup-form.html', **params)
		else: 
			theory = Theory.get_by_username(username)
			if theory:
				message = 'That username already exists!'
				self.print_html('signup-form.html', error_username = message)
			else:
				theory = Theory.register(username, password, email)
				theory.put()
				self.login(theory)
				self.redirect('/important-people')


class Login(Handler):
	def get(self):
		self.print_html('login-form.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		theory = Theory.valid_login(username, password)
		if theory:
			self.login(theory)
			self.redirect('/important-people')
		else:
			message = "Incorrect Username or Password"
			self.print_html('login-form.html', error = message)


class Logout(Handler):
	def get(self):
		self.logout()
		self.redirect('/')


class ImportantPeople(Handler):
	
	
	def get(self):
		theory = self.theory
		# people = theory.kas1
		people = my_important_people(theory)
		mission = todays_mission(theory)
		self.print_html('important-people.html', people=people, mission=mission)
	
	def post(self):
		theory = self.theory
		name = self.request.get('important_person_name')
		frequency = self.request.get('frequency')
		details = dict(frequency=frequency, imp_person_name=name)
		add_important_person_to_theory(theory, details)
		self.redirect('/important-people')



class Mission(Handler):

	def get(self):
		theory = self.theory
		if theory:
			mission = todays_mission(theory)
			self.print_html('todays-mission.html', mission=mission)
		else:
			self.redirect('/login')


	def post(self):
		theory = self.theory
		ksu_set = eval(theory.kas1, {})
		master_log = eval(theory.master_log, {})
		target_ksu = int(self.request.get('ksu_id_digit'))
		ksu = ksu_set[target_ksu]
		post_details = get_post_details(self)
		# self.response.write(post_details)
		event = effort_event(post_details)
		add_event_to_ksu(ksu,event)
		update_next_exe(ksu)
		update_master_log(master_log, event)
		theory.master_log = str(master_log)
		theory.kas1 = str(ksu_set)
		theory.put()
		self.redirect('/mission')








class Email(Handler):
    def get(self):
    	theories = Theory.all().fetch(limit=10)
    	for theory in theories:
    		email_receiver = str(theory.email)
    		email_body = mission_email(todays_mission(theory))
    		mail.send_mail(sender="<mission@kasware100.appspotmail.com>", to=email_receiver, subject="Today's Mission", body=email_body)
		self.response.write('Emails sent!')




class LoadCSV(Handler):
	def get(self):
		theory = self.theory
		add_ksus_to_set_from_csv(csv_path, theory)
		self.redirect('/important-people')




class PythonBackup(Handler):
	def get(self):
		theory = self.theory
		if theory:
			kas1 = theory.kas1
			self.write(kas1)
		else:
			self.redirect('/login')




class CSVBackup(Handler):
	def get(self):
		theory = self.theory
		if theory:
			kas1 = eval(theory.kas1, {})
			output = create_csv_backup(kas1, ['ksu_id','ksu_type','description','frequency','lastest_exe','status','imp_person_name'])
			self.write(output)
		else:
			self.redirect('/login')




# --- Datastore Entities ----------------------------------------------------------------------------

class Theory(db.Model):
	username = db.StringProperty(required=True)
	password_hash = db.StringProperty(required=True)
	email = db.StringProperty(required=True)
	kas1 = db.TextProperty(required=True)
	master_log = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)

	@classmethod # This means you can call a method directly on the Class (no on a Class Instance)
	def get_by_theory_id(cls, theory_id):
		return Theory.get_by_id(theory_id)

	@classmethod
	def get_by_username(cls, username):
		return Theory.all().filter('username =', username).get()

	@classmethod #Creates the theory object but do not store it in the db
	def register(cls, username, password, email):
		password_hash = make_password_hash(username, password)
		return Theory(username=username, password_hash=password_hash, email=email, kas1=new_kas1(), master_log=new_master_log())

	@classmethod
	def valid_login(cls, username, password):
		theory = cls.get_by_username(username)
		if theory and validate_password(username, password, theory.password_hash):
			return theory




# --- Helper Functions -----------------------------------------------------------------------------
#--- Security Functions ---

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return email and EMAIL_RE.match(email)

def make_secure_val(val):
    return '%s|%s' % (val, hashlib.sha256(secret + val).hexdigest())

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val

def make_salt(lenght = 5):
    return ''.join(random.choice(string.letters) for x in range(lenght))

def make_password_hash(username, password, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(username + password + salt).hexdigest()
	return '%s|%s' % (h, salt)

def validate_password(username, password, h):
	salt = h.split('|')[1]
	return h == make_password_hash(username, password, salt)



#--- Handler Essentials ---

def get_post_details(self):
	result = new_event()
	arguments = self.request.arguments()
	for argument in arguments:
		result[str(argument)] = self.request.get(str(argument))
	return result


def update_next_exe(ksu):
	frequency = int(ksu['frequency'])
	next_exe = today + frequency
	ksu['next_exe'] = next_exe
	ksu['lastest_exe'] = today
	return



#--- New KSU & KSU set --- 

def ksu_template():
	template = {'ksu_id': None,
				'ksu_id_digit': None,
		   		'ksu_type': None,
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
		    	'priority_lvl':9,
		    	'is_critical': False,
		    	'comments': None,
		    	'lastest_exe':None, 
		    	'next_exe':None,
		    	'target_exe':None,
		    	'in_mission': False,
		    	'is_visible': True,
		    	'is_private' False,
		    	'status':'Active',
		    	'start_date':None,
		    	'end_date':None,
		    	'action_nature':None, # Enjoy or Produce
		    	'internalization_lvl':None,
		    	'kas4_valid_exceptions':None,
		    	'kas3_triger_condition': None,
		    	'bigo_eval_date':None,
		    	'bigo_type':None, # End Goal or Sprint Goal
		    	'wish_excitement_lvl':None,
		    	'imp_person_name':None,
		    	'history':None}
	return template		    	



def new_master_log(start_date=735942, end_date=736680):
	result = {}
	for date in range(start_date, end_date):
		entry = {'date':0,'Effort':0,'Happiness':0}
		entry['date'] = datetime.fromordinal(date).strftime('%d-%m-%Y')
		result[date] = entry
	return str(result)



def new_kas1():
	result = []
	first_ksu = ksu_template()
	first_ksu['ksu_id'] = 'kas1_0'
	first_ksu['ksu_type'] = 'kas1'
	first_ksu['description'] = 'KAS1 Key Base Actions Set'
	result.append(first_ksu)
	return str(result)



def new_ksu(ksu_set):
	ksu_type = ksu_set[0]['ksu_type']
	id_digit = len(ksu_set)
	ksu_id = ksu_type + '_'+ str(id_digit)
	event = new_event()
	event['event_type'] = 'Created'
	new_ksu = ksu_template()
	new_ksu['ksu_id'] = ksu_id
	new_ksu['ksu_id_digit'] = id_digit
	new_ksu['ksu_type'] = ksu_type
	new_ksu['history'] = [event]
	return new_ksu






#--- Event related ---


def new_event():
	event = {'event_date':today,
			 'event_type':None, # [Created, Edited ,Deleted, Happiness, Effort]
			 'event_duration':0, # In minutes rounded down
			 'event_value':0, # In a fibonacci scale
			 'event_comments':None} # Passed in as as an optinal parameter
	return event


def add_effort_event_to_ksu(ksu, post_details):
	event = new_event()
	event['event_type'] = 'Effort'
	event['event_comments'] = post_details['event_comments']
	event['event_duration'] = post_details['event_duration']
	event_points['event_value'] = ksu['base_effort_points']
	history = ksu['history']
	history.append(event)
	ksu['history'] = history
	return

def effort_event(post_details):
	event = new_event()
	event['event_type'] = 'Effort'
	event['event_comments'] = post_details['event_comments']
	event['event_duration'] = post_details['event_duration']
	event['event_value'] = post_details['event_value']
	return event


def happiness_event(post_details):
	event = new_event()
	event['event_type'] = 'Happiness'
	event['event_comments'] = post_details['event_comments']
	event['event_duration'] = post_details['event_duration']
	event['event_value'] = int(post_details['event_duration']) * int(post_details['event_base_intensity']) + int(post_details['event_spike_intensity'])
	return event


def add_event_to_ksu(ksu, event):
	history = ksu['history']
	history.append(event)
	ksu['history'] = history
	return


def update_master_log(master_log, event):
	date = event['event_date']
	event_type = event['event_type']
	event_points = int(event['event_value'])
	log = master_log[date]
	log[event_type] = log[event_type] + event_points
	return










#--- Important People related ---


def add_important_person_to_theory(theory, details):
	ksu_set = eval(theory.kas1, {})
	ksu = new_ksu(ksu_set)
	ksu['ksu_subtype'] = 'Important_Person'
	ksu['element'] = '4_Love_Friendship'
	ksu['description'] = 'Contactar a ' + details['imp_person_name']
	ksu['next_exe'] = today + int(details['frequency'])
	ksu['base_effort_points'] = 3
	for key, value in details.iteritems():
		ksu[key] = value
	ksu_set.append(ksu)
	theory.kas1 = str(ksu_set)
	theory.put()
	return



def my_important_people(theory):
	kas1 = eval(theory.kas1, {})
	result = []
	for ksu in kas1:
		if ksu['ksu_subtype'] == 'Important_Person':
			result.append(ksu)
	return result





#--- Mission related ---

def todays_mission(theory):
	ksu_set = eval(theory.kas1, {})
	result = []
	for ksu in ksu_set:
		if ksu['next_exe']:
			delay = today - int(ksu['next_exe'])
			status = ksu['status']
			if delay >= 0 and status=='Active':
				result.append(ksu)
	return result



def mission_email(ksu_set):
	result = "Hello, here is your mission for today: " 
	space = """
"""
	for ksu in ksu_set:
		result += space + space + ksu['description']
	result += space + space + space + space + "visit www.kasware.com to update your mission status"
	return result






#--- CSV load & backup ---

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



def add_ksus_to_set_from_csv(csv_path, theory):
	ksu_set = eval(theory.kas1, {})
	digested_csv = digest_csv(csv_path)
	for pseudo_ksu in digested_csv:
		ksu = new_ksu(ksu_set)
		for key, value in pseudo_ksu.iteritems():
			ksu[key] = value
		ksu_set.append(ksu)
	theory.kas1 = str(ksu_set)
	theory.put()
	return


def create_csv_backup(ksu_set, required_attributes):
	result = ""
	i = 0
	for attribute in required_attributes:
		result += attribute + ',' 
	for ksu in ksu_set:
		result += '<br>'
		for attribute in required_attributes:
			result += str(ksu[attribute]) + ','
	return result




# --- Global Variables ------------------------------------------------------------------------------

today = datetime.today().toordinal() + 14

list_elements_cat = ['1. Fun & Excitement', 
					 '2. Meaning & Direction', 
					 '3. Health & Vitality', 
					 '4. Love & Friendship', 
					 '5. Knowledge & Skills', 
					 '6. Outer Peace', 
					 '7. Money & Resources', 
					 '8. Inner Peace']

secret = 'elzecreto'



# csv_path = '/Users/amigabledave/kasware100/csv_files/important_people.csv'

csv_path = os.path.join(os.path.dirname(__file__), 'csv_files', 'important_people.csv')


# --- Regular expressions ---

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')



# --- URL Handler Relation ---------------------------------------------------------------------------

app = webapp2.WSGIApplication([
							 ('/', Home),
							 ('/signup', Signup),
							 ('/login', Login),
                             ('/logout', Logout),
                             ('/mission', Mission),
							 ('/important-people',ImportantPeople),
							 ('/email',Email),
							 ('/loadCSV', LoadCSV),
							 ('/python-backup',PythonBackup),
							 ('/csv-backup',CSVBackup)
							 ], debug=True)
