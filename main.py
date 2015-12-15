#KASware v1.0.0 | Copyright 2015 AmigableDave & Co.

import re, os, webapp2, jinja2, logging, hashlib, random, string, csv, pickle
from datetime import datetime, timedelta
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import mail


template_dir = os.path.join(os.path.dirname(__file__), 'html_templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)



# --- Datastore Entities ----------------------------------------------------------------------------

class Theory(db.Model):
	username = db.StringProperty(required=True)
	password_hash = db.StringProperty(required=True)
	email = db.StringProperty(required=True)
	kas1 = db.TextProperty(required=True)
	master_log = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	history_1 = db.TextProperty(required=True)

	@classmethod # This means you can call a method directly on the Class (no on a Class Instance)
	def get_by_theory_id(cls, theory_id):
		return Theory.get_by_id(theory_id)

	@classmethod
	def get_by_username(cls, username):
		return Theory.all().filter('username =', username).get()

	@classmethod #Creates the theory object but do not store it in the db
	def register(cls, username, password, email):
		password_hash = make_password_hash(username, password)
		return Theory(username=username, password_hash=password_hash, email=email, kas1=new_kas1(), master_log=new_master_log(), history_1=new_history())

	@classmethod
	def valid_login(cls, username, password):
		theory = cls.get_by_username(username)
		if theory and validate_password(username, password, theory.password_hash):
			return theory





# --- Handlers -------------------------------------------------------------------------------------------


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_html(self, template, **kw):
		t = jinja_env.get_template(template)
		if self.theory:
			theory = self.theory
			todays_effort = unpack_set(theory.master_log)[today]['Effort']
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





#--- Important People Handler ---


class ImportantPeople(Handler):
	
	
	def get(self):
		theory = self.theory
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



def add_important_person_to_theory(theory, details):
	ksu_set = unpack_set(theory.kas1)
	history = unpack_set(theory.history_1)
	ksu = new_ksu_in_kas1(ksu_set)
	ksu['ksu_subtype'] = 'Important_Person'
	ksu['element'] = 'E500'
	ksu['description'] = 'Contactar a ' + details['imp_person_name']
	ksu['next_exe'] = today + int(details['frequency'])
	ksu['effort_points'] = 3
	event = new_event()
	event['type'] = 'Created'
	event['ksu_id'] = ksu['ksu_id']
	update_history(history, event)
	for key, value in details.iteritems():
		ksu[key] = value
	ksu_set.append(ksu)
	theory.history_1 = pack_set(history)
	theory.kas1 = pack_set(ksu_set)
	theory.put()
	return



def my_important_people(theory):
	kas1 = unpack_set(theory.kas1)
	result = []
	for ksu in kas1:
		if ksu['ksu_subtype'] == 'Important_Person':
			result.append(ksu)
	result = pretty_dates(result)
	return result




def pretty_dates(ksu_set):
	date_attributes = ['latest_exe', 'next_exe']
	for date_attribute in date_attributes:
		for ksu in ksu_set:
			if ksu[date_attribute]:
				number_date = int(ksu[date_attribute])
				pretty_date = datetime.fromordinal(number_date).strftime('%b %d')
				# pretty_date = datetime.fromordinal(number_date).strftime('%a-%d-%m-%Y')
				ksu[date_attribute] = pretty_date
	return ksu_set
	



#--- Mission Handler ---


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
		ksu_set = unpack_set(theory.kas1)
		master_log = unpack_set(theory.master_log)
		history = unpack_set(theory.history_1)
		target_ksu = get_digit_from_id(self.request.get('ksu_id'))
		ksu = ksu_set[target_ksu]
		post_details = get_post_details(self)
		event = effort_event(post_details)
		update_history(history, event)
		update_next_exe(ksu) # BUG ALERT! This will not work for all KSU types
		update_master_log(master_log, event)
		theory.history_1 = pack_set(history)
		theory.master_log = pack_set(master_log)
		theory.kas1 = pack_set(ksu_set)
		theory.put()
		self.redirect('/mission')


def get_digit_from_id(ksu_id):
	return int(ksu_id.split("_")[1])


def todays_mission(theory):
	ksu_set = unpack_set(theory.kas1)
	result = []
	for ksu in ksu_set:
		if ksu['next_exe']:
			delay = today - int(ksu['next_exe'])
			status = ksu['status']
			if delay >= 0 and status=='Active':
				result.append(ksu)
	return result




#--- Effort Report Handler --- BUG ALERT! Pending to update given the new KSU structure


class EffortReport(Handler):
	def get(self):
		theory = self.theory
		report = create_effort_report(theory,today)
		self.print_html('effort-report.html', report=report)




def get_attribute_from_id(ksu_set, ksu_id, ksu_attribute):
	result = None
	for ksu in ksu_set:
		if ksu['ksu_id'] == ksu_id:
			result = ksu[ksu_attribute]
	return result



def create_effort_report(theory, date):
	result = []
	kas1 = unpack_set(theory.kas1)
	history = unpack_set(theory.history_1)
	for event in history:
		if event['date'] == date and event['type']=='Effort':			
			report_item = {'effort_description':None,'effort_points':0}
			report_item['effort_description'] = get_attribute_from_id(kas1, event['ksu_id'], 'description')
			report_item['effort_points'] = event['value']
			result.append(report_item)
	return result





#--- Email Handler ---


class Email(Handler):
    def get(self):
    	theories = Theory.all().fetch(limit=10)
    	for theory in theories:
    		email_receiver = str(theory.email)
    		email_body = mission_email(todays_mission(theory))
    		mail.send_mail(sender="<mission@kasware100.appspotmail.com>", to=email_receiver, subject="Today's Mission", body=email_body)
		self.response.write('Emails sent!')

def mission_email(ksu_set):
	result = "Hello, here is your mission for today: " 
	space = """
"""
	for ksu in ksu_set:
		result += space + space + ksu['description']
	result += space + space + space + space + "visit www.kasware.com to update your mission status"
	return result






class LoadCSV(Handler):
	def get(self):
		theory = self.theory
		add_ksus_to_set_from_csv(csv_path, theory)
		self.redirect('/important-people')




class PythonBackup(Handler):
	def get(self):
		theory = self.theory
		if theory:
			kas1 = unpack_set(theory.kas1)
			self.write(kas1)
		else:
			self.redirect('/login')




class CSVBackup(Handler):
	def get(self):
		theory = self.theory
		if theory:
			kas1 = unpack_set(theory.kas1)
			output = create_csv_backup(kas1, ['ksu_id','description','frequency','latest_exe','status','imp_person_name'])
			self.write(output)
		else:
			self.redirect('/login')



class History(Handler):
	def get(self):
		theory = self.theory
		if theory:
			history = unpack_set(theory.history_1)
			self.write(history)
		else:
			self.redirect('/login')




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
	ksu['latest_exe'] = today
	return






#--- New KSU & KSU set --- 



def ksu_template():
	template = {'ksu_id': None,	
				'ksu_subtype':None,			
		    	'element': None,
		    	'description': None,
		    	'comments': None,
		    	'local_tags': None,
		    	'global_tags': None,
		    	'parent_ksu_id': None,
		    	'priority_lvl':9,
		    	'is_critical': False,
		    	'is_visible': True,
		    	'is_private': False}
	return template	



def create_ksu_id(ksu_set):
	ksu_type = ksu_set[0]['ksu_type']
	id_digit = int(ksu_set[0]['set_size']) + 1
	ksu_set[0]['set_size'] = id_digit
	ksu_id = ksu_type + '_'+ str(id_digit)
	return ksu_id


def new_ksu_in_kas1(kas1):
	ksu = ksu_template()
	ksu_id = create_ksu_id(kas1)
	ksu['ksu_id'] = ksu_id
	ksu['status'] = 'Active' # ['Active', 'Hold', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['frequency'] = None
	ksu['best_day'] = None
	ksu['best_time'] = None
	ksu['latest_exe'] = None
	ksu['next_exe'] = None
	ksu['target_exe'] = None
	ksu['imp_person_name'] = None
	return ksu



def new_ksu_in_kas2(kas2):
	ksu = ksu_template()
	ksu_id = create_ksu_id(kas2)
	ksu['ksu_id'] = ksu_id
	ksu['status'] = 'Pending' # ['Done', 'Pending', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['best_time'] = None
	ksu['target_exe'] = None
	return ksu





def new_master_log(start_date=735942, end_date=736680):
	result = {}
	for date in range(start_date, end_date):
		entry = {'date':0,'Effort':0,'Happiness':0}
		entry['date'] = datetime.fromordinal(date).strftime('%d-%m-%Y')
		result[date] = entry
	return pack_set(result)


def new_history():
	result = []
	event = new_event()
	event['type'] = 'Created'
	result.append(event)
	return pack_set(result)



def new_kas1():
	result = []
	ksu = ksu_template()
	ksu['set_size'] = 0
	ksu['ksu_id'] = 'kas1_0'
	ksu['ksu_type'] = 'kas1'
	ksu['description'] = 'KAS1 Key Base Actions Set'
	ksu['status'] = 'Active' # ['Active', 'Hold', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['frequency'] = None
	ksu['best_day'] = None
	ksu['best_time'] = None
	ksu['latest_exe'] = None
	ksu['next_exe'] = None
	ksu['target_exe'] = None
	ksu['imp_person_name'] = None
	ksu['is_visible'] = False
	#BUG ALERT - Pending to add create and add an event to master log
	# event = new_event()
	# event['event_type'] = 'Created'
	# first_ksu['history'] = [event]
	result.append(ksu)
	return pack_set(result)







#--- Event related ---


def new_event():
	event = {'type':None, # [Created, Edited ,Deleted, Happiness, Effort]
			 'ksu_id': None,
			 'element': None, # This is only here because KAS2 skus will be deleted
			 'description': None, # Passed in as as an optional parameter
			 'date':today,
			 'duration':0, #To record duration of happy moments
			 'value':0} # In a fibonacci scale
	return event



def update_history(history, event):
	history.append(event)
	return



def effort_event(post_details):
	event = new_event()
	event['ksu_id'] = post_details['ksu_id']
	event['type'] = 'Effort'
	event['description'] = post_details['event_comments']
	event['duration'] = post_details['event_duration']
	event['value'] = post_details['event_value']
	return event





#BUG WARNING - NEEDS TO BE FIXED TO NEW VERSION
def update_master_log(master_log, event):
	date = event['date']
	event_type = event['type']
	event_value = int(event['value'])
	log = master_log[date]
	log[event_type] = log[event_type] + event_value
	return





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
	ksu_set = unpack_set(theory.kas1)
	history = unpack_set(theory.history_1)
	digested_csv = digest_csv(csv_path)
	for pseudo_ksu in digested_csv:
		ksu = new_ksu_in_kas1(ksu_set)
		event = new_event()
		event['ksu_id'] = ksu['ksu_id']
		event['type'] = 'Created'
		update_history(history, event)
		for key, value in pseudo_ksu.iteritems():
			ksu[key] = value
		ksu_set.append(ksu)
	theory.history_1 = pack_set(history)
	theory.kas1 = pack_set(ksu_set)
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



#--- Pickle related ---

def pack_set(ksu_set):
	return pickle.dumps(ksu_set)

def unpack_set(ksu_pickled_set):
	return pickle.loads(ksu_pickled_set)






# --- Global Variables ------------------------------------------------------------------------------

today = datetime.today().toordinal()

dictionary_Elements = {'E100': '1. Inner Peace',
					 'E200': '2. Fun & Excitement', 
					 'E300': '3. Meaning & Direction', 
					 'E400': '4. Health & Vitality', 
					 'E500': '5. Love & Friendship', 
					 'E600': '6. Knowledge & Skills', 
					 'E700': '7. Outer Peace', 
					 'E800': '8. Monetary Resources',
				 	 'E900': '9. Non-Monetary Resources'}




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
							 ('/effort-report',EffortReport),
							 ('/email',Email),
							 ('/loadCSV', LoadCSV),
							 ('/python-backup',PythonBackup),
							 ('/csv-backup',CSVBackup),
							 ('/history', History)
							 ], debug=True)
