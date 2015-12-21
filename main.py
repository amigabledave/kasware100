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
	KAS1 = db.TextProperty(required=True)
	ImPe = db.TextProperty(required=True)
	master_log = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	history = db.TextProperty(required=True)

	@classmethod # This means you can call a method directly on the Class (no on a Class Instance)
	def get_by_theory_id(cls, theory_id):
		return Theory.get_by_id(theory_id)

	@classmethod
	def get_by_username(cls, username):
		return Theory.all().filter('username =', username).get()

	@classmethod #Creates the theory object but do not store it in the db
	def register(cls, username, password, email):
		password_hash = make_password_hash(username, password)
		return Theory(username=username, 
					  password_hash=password_hash,
					  email=email, 
					  KAS1=new_set_KAS1(),
					  ImPe=new_set_ImPe(),
					  master_log=new_set_master_log(),
					  history=new_set_history())

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
		user_Action_Effort_Done(self)
		self.redirect('/mission')



def todays_mission(theory):
	ksu_set = unpack_set(theory.KAS1)
	result = []
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		if ksu['next_exe']:
			delay = today - int(ksu['next_exe'])
			status = ksu['status']
			if delay >= 0 and status=='Active':
				result.append(ksu)
	return result



#--- Set Viewer Handler ---

class SetViewer(Handler):
	def get(self, set_name):
		theory = self.theory
		if theory:
			ksu_set = unpack_set(eval('theory.' + set_name))
			set_details = ksu_set['set_details']
			ksu_set = pretty_dates(ksu_set)
			ksu_set = hide_invisible(ksu_set)
			ksu_set = list(ksu_set.values())
			viewer_details = d_Viewer[set_name]
			self.print_html('set-viewer.html', viewer_details=viewer_details, ksu_set=ksu_set)
		else:
			self.redirect('/login')




#--- Important People Handler ---


class ImportantPeople(Handler):
	
	def get(self):
		theory = self.theory
		people = pretty_dates(unpack_set(theory.ImPe))
		people = list(people.values())
		self.print_html('important-people.html', people=people)
	
	def post(self):
		user_Action_Create_ImPe_ksu(self)
		self.redirect('/important-people')




def pretty_dates(ksu_set):
	date_attributes = ['latest_exe', 'next_exe', 'last_contact', 'next_contact']
	for date_attribute in date_attributes:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]
			valid_attributes = list(ksu.keys())
			if date_attribute in valid_attributes:	
				if ksu[date_attribute]:
					number_date = int(ksu[date_attribute])
					pretty_date = datetime.fromordinal(number_date).strftime('%b %d, %Y')
					# pretty_date = datetime.fromordinal(number_date).strftime('%a-%d-%m-%Y')
					ksu[date_attribute] = pretty_date
	return ksu_set
	


def hide_invisible(ksu_set):
	result = {}
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		if ksu['is_visible']:
			result[ksu['id']] = ksu
	return result





#--- New KSU Handler ---

class NewKSU(Handler):
	def get(self):
		self.print_html('ksu-new-form.html', constants=constants)





#--- Edit KSU Handler ---

class EditKSU(Handler):
	def get(self):
		self.print_html('ksu-edit-form.html', elements=list_Elements)




#--- Effort Report Handler --- 

class EffortReport(Handler):
	def get(self):
		theory = self.theory
		report = create_effort_report(theory,today)
		self.print_html('effort-report.html', report=report)



def get_attribute_from_id(ksu_set, ksu_id, ksu_attribute):
	return ksu_set[ksu_id][ksu_attribute]



def create_effort_report(theory, date):
	result = []
	KAS1 = unpack_set(theory.KAS1)
	history = unpack_set(theory.history)
	for event in history:
		event = history[event]
		if event['date'] == date and event['type']=='Effort':			
			report_item = {'effort_description':None,'effort_points':0}
			report_item['effort_description'] = get_attribute_from_id(KAS1, event['ksu_id'], 'description')
			report_item['effort_points'] = event['value']
			result.append(report_item)
	return result





#--- Development Handlers --------

#--- Load CSV  ---

class LoadCSV(Handler):
	def get(self):
		developer_Action_Load_ImPe_CSV(self,ImPe_csv_path)
		self.redirect('/important-people')



#--- Create CSV Backup ---

class CSVBackup(Handler):
	def get(self):
		theory = self.theory
		if theory:
			KAS1 = unpack_set(theory.KAS1)
			output = create_csv_backup(KAS1, ['id','description','frequency','latest_exe','status'])
			self.write(output)
		else:
			self.redirect('/login')


def create_csv_backup(ksu_set, required_attributes):
	result = ""
	i = 0
	for attribute in required_attributes:
		result += attribute + ',' 
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		result += '<br>'
		for attribute in required_attributes:
			result += str(ksu[attribute]) + ','
	return result




#--- Send Email ---


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





#--- Raw Data Viewer ---


class PythonBackup(Handler):

	def get(self, set_name):
		theory = self.theory
		if theory:
			ksu_set = unpack_set(eval('theory.' + set_name))
			self.write(ksu_set)
		else:
			self.redirect('/login')






# --- Additional Helper Functions -----------------------------------------------------------------------------

#--- Essentials ---


def get_post_details(self):
	result = {}
	arguments = self.request.arguments()
	for argument in arguments:
		result[str(argument)] = self.request.get(str(argument))
	return result

def pack_set(ksu_set):
	return pickle.dumps(ksu_set)


def unpack_set(ksu_pickled_set):
	return pickle.loads(ksu_pickled_set)


def get_digit_from_id(ksu_id):
	return int(ksu_id.split("_")[1])


def get_type_from_id(ksu_id):
	return ksu_id.split("_")[0]





#--- Update Stuff ---


def update_ksu_next_exe(theory, post_details):
	ksu_set = unpack_set(theory.KAS1)
	ksu_id = post_details['ksu_id']
	ksu = ksu_set[ksu_id]
	ksu['next_exe'] = today + int(ksu['frequency'])
	ksu['latest_exe'] = today
	theory.KAS1 = pack_set(ksu_set)
	return



def update_master_log(theory, event):
	master_log = unpack_set(theory.master_log)

	date = event['date']
	event_type = event['type']
	if event_type == 'Effort' or event_type == 'Happiness':
		event_value = int(event['value'])
		log = master_log[date]
		log[event_type] = log[event_type] + event_value

	ksu_id = event['ksu_id']
	event_id = event['id']
	if ksu_id in master_log:
		ksu_history = master_log[ksu_id]
		ksu_history.append(event_id)
	else:
		ksu_history = [event_id]
	master_log[ksu_id] = ksu_history

	set_name = get_type_from_id(ksu_id)
	ksu_set = unpack_set(eval("theory." + set_name)) 
	ksu = ksu_set[ksu_id]
	person_id = ksu['target_person']
	if person_id:
		if person_id in master_log:
			person_history = master_log[person_id]
			person_history.append(event_id)
		else:
			person_history = [event_id]
		master_log[person_id] = person_history

	theory.master_log = pack_set(master_log)
	return






#--- Dictionary Templates ---

def event_template():
	event = {'id': None,
			 'type':None, # [Created, Edited ,Deleted, Happiness, Effort]
			 'ksu_id':None,
			 'description': None, # Comments regarding the event
			 'date':today,
			 'duration':0, #To record duration of happy moments
			 'value':0} # In a fibonacci scale
	return event


def ksu_template():
	template = {'id': None,	
				'subtype':None,		
		    	'element': None,
		    	'purpose':None,
		    	'description': None,
		    	'comments': None,
		    	'local_tags': None,
		    	'global_tags': None,
		    	'target_person':None,
		    	'parent_id': None,
		    	'priority_lvl':9,
		    	'is_critical': False,
		    	'is_visible': True,
		    	'is_private': False}
	return template	


def important_person_template():
	person = {'id':None,
			  'name':None,
			  'target_person':None, # Attribute needed just to avoid KeyErrors
			  'is_visible': True, # Attribute needed just to avoid KeyErrors
			  'group':None,
			  'contact_frequency':None,
			  'last_contact':None,
			  'next_contact':None,
			  'fun_facts':None,
			  'email':None,
			  'phone':None,
			  'facebook':None,
			  'birthday':None,
			  'comments':None,
			  'important_since':today,
			  'child_ksus':[],
			  'related_ksus':[]}
	return person




#--- Create new Sets --- 



def new_set_history():
	result = {}
	event = event_template()
	event['id'] = 'Event_0'
	event['type'] = 'Created'
	event['set_type'] = 'Event'
	event['set_size'] = 0
	event['description'] = 'Events History'
	result['set_details'] = event
	return pack_set(result)



def new_set_master_log(start_date=(735964-31), end_date=(735964+366)): #start_date = Dec 1, 2015 |  end_date = Dec 31, 2016
	result = {}
	for date in range(start_date, end_date):
		entry = {'Effort':0,'Happiness':0}
		entry['date'] = datetime.fromordinal(date).strftime('%d-%m-%Y')
		result[date] = entry
	return pack_set(result)



def new_set_KAS1():
	result = {}
	ksu = ksu_template()
	ksu['set_size'] = 0
	ksu['id'] = 'KAS1_0'
	ksu['set_type'] = 'KAS1'
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
	ksu['is_visible'] = False
	result['set_details'] = ksu
	return pack_set(result)



def new_set_ImPe():
	result = {}
	ksu = important_person_template()
	ksu['set_size'] = 0
	ksu['id'] = 'ImPe_0'
	ksu['set_type'] = 'ImPe'
	ksu['description'] = 'My Important People'
	ksu['is_visible'] = False
	result['set_details'] = ksu
	return pack_set(result)




#--- Create new Set Items ---

def create_id(ksu_set):
	set_details = ksu_set['set_details']
	set_type = set_details['set_type']
	id_digit = int(set_details['set_size']) + 1
	set_details['set_size'] = id_digit
	ksu_id = set_type + '_'+ str(id_digit)
	return ksu_id


def new_event(history):
	event = event_template()
	event_id = create_id(history)
	event['id'] = event_id
	return event


def new_ksu_for_KAS1(KAS1):
	ksu = ksu_template()
	ksu_id = create_id(KAS1)
	ksu['id'] = ksu_id
	ksu['status'] = 'Active' # ['Active', 'Hold', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['frequency'] = None
	ksu['best_day'] = None
	ksu['best_time'] = None
	ksu['latest_exe'] = None
	ksu['next_exe'] = None
	return ksu


def new_ksu_for_ImPe(Important_People_set):
	ksu = important_person_template()
	ksu_id = create_id(Important_People_set)
	ksu['id'] = ksu_id
	return ksu


def new_ksu_for_KAS2(KAS2):
	ksu = ksu_template()
	ksu_id = create_id(kas2)
	ksu['id'] = ksu_id
	ksu['status'] = 'Pending' # ['Done', 'Pending', 'Deleted']
	ksu['effort_points'] = 0
	ksu['in_mission'] = False
	ksu['best_time'] = None
	ksu['target_exe'] = None
	return ksu



#--- Add items to sets. IT DOES NOT STORE THEM, IS STILL NECESARY TO ADD THE FUNCTION 	theory.put() ---

def update_set(ksu_set, ksu):
	ksu_id = ksu['id']
	ksu_set[ksu_id]=ksu
	return


def add_Created_event(theory, ksu):
	history = unpack_set(theory.history)
	event = new_event(history)
	event['type'] = 'Created'
	event['ksu_id'] = ksu['id']
	update_set(history, event)
	update_master_log(theory, event)
	theory.history = pack_set(history)
	return event



def add_Effort_event(theory, post_details):
	history = unpack_set(theory.history)
	event = new_event(history)
	event['ksu_id'] = post_details['ksu_id']
	event['type'] = 'Effort'
	event['description'] = post_details['event_comments']
	event['duration'] = post_details['event_duration']
	event['value'] = post_details['event_value']
	update_set(history, event)
	update_master_log(theory, event)
	theory.history = pack_set(history)
	return event



def add_Person_ksu(theory, post_details):
	ImPe = unpack_set(theory.ImPe)
	person = new_ksu_for_ImPe(ImPe)
	person['name'] = post_details['name']
	person['contact_frequency'] = post_details['contact_frequency']
	person['next_contact'] = today + int(post_details['contact_frequency'])
	if 'last_contact' in post_details:
		person['last_contact'] = post_details['last_contact']
	update_set(ImPe,person)
	theory.ImPe = pack_set(ImPe)
	return person




def add_ImPe_Contact_ksu(theory, person):
	KAS1 = unpack_set(theory.KAS1)
	ksu = new_ksu_for_KAS1(KAS1)
	ksu['element'] = 'E500'
	ksu['description'] = 'Contactar a ' + person['name']
	ksu['frequency'] = person['contact_frequency']
	if person['last_contact']:
		ksu['latest_exe'] = person['last_contact']
		ksu['next_exe'] = int(person['last_contact']) + int(person['contact_frequency'])
	else:
		ksu['next_exe'] = today + int(person['contact_frequency'])
	ksu['effort_points'] = 3
	ksu['target_person'] = person['id']
	ksu['subtype'] = 'ImPe_Contact'
	person['child_ksus'] = person['child_ksus'].append(ksu['id'])
	update_set(KAS1,ksu)
	theory.KAS1 = pack_set(KAS1)
	return ksu





#--- User Actions ---

def user_Action_Effort_Done(self):
	theory = self.theory
	post_details = get_post_details(self)
	update_ksu_next_exe(theory, post_details)
	add_Effort_event(theory, post_details)
	theory.put()


def user_Action_Create_ImPe_ksu(self):
	theory = self.theory
	details = get_post_details(self)
	person = add_Person_ksu(theory, details)
	ksu = add_ImPe_Contact_ksu(theory, person)
	add_Created_event(theory,person)
	add_Created_event(theory, ksu)
	theory.put()




#--- Developer Actions ---

def developer_Action_Load_ImPe_CSV(self,csv_path):
	theory = self.theory
	f = open(csv_path, 'rU')
	f.close
	csv_f = csv.reader(f, dialect=csv.excel_tab)
	attributes = csv_f.next()[0].split(',')
	for row in csv_f:
		digested_ksu = {}
		i = 0
		raw_ksu = row[0].split(',')
		for attribute in raw_ksu:
			digested_ksu[attributes[i]] = attribute
			i += 1
		details = digested_ksu
		person = add_Person_ksu(theory, details)
		ksu = add_ImPe_Contact_ksu(theory, person)
		add_Created_event(theory,person)
		add_Created_event(theory, ksu)
	theory.put()
	return 




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




# --- Global Variables ------------------------------------------------------------------------------

today = datetime.today().toordinal()



l_Elements = ['1. Inner Peace',
			 '2. Fun & Excitement',
			 '3. Meaning & Direction', 
			 '4. Health & Vitality',
			 '5. Love & Friendship',
			 '6. Knowledge & Skills',
			 '7. Outer Peace',
			 '8. Monetary Resources',
			 '9. Non-Monetary Resources']



l_Purposes = ['1. Create Moments',
			 '2. Generate Resources',
			 '3. Avoid Shit']



l_Days = [ None,
		  'Sunday',
		  'Monday',
		  'Tuesday',
		  'Wednesday',
		  'Thursday',
		  'Friday',
		  'Saturday']



d_Elements = {'E100': '1. Inner Peace',
			 'E200': '2. Fun & Excitement', 
			 'E300': '3. Meaning & Direction', 
			 'E400': '4. Health & Vitality', 
			 'E500': '5. Love & Friendship', 
			 'E600': '6. Knowledge & Skills', 
			 'E700': '7. Outer Peace', 
			 'E800': '8. Monetary Resources',
		 	 'E900': '9. Non-Monetary Resources'}



constants = {'l_Elements':l_Elements,
			 'l_Purposes':l_Purposes,
			 'l_Days':l_Days,
			 'd_Elements':d_Elements}



d_Viewer ={'KAS1':{'set_name':'My Key Base Actions Set  (KAS1)',
				   'attributes':['description','frequency','latest_exe','next_exe','comments'],
				   'fields':{'description':'Description','frequency':'E. Freq.','latest_exe':'Last Event','next_exe':'Next Event','comments':'Comments'},
				   'columns':{'description':3,'frequency':1,'latest_exe':2,'next_exe':2,'comments':3}},
		   
		   'ImPe': {'set_name':'My Important People',
					'attributes':['name', 'contact_frequency', 'last_contact', 'next_contact', 'comments'],
				    'fields':{'name':'Name', 'contact_frequency':'C. Freq.', 'last_contact':'Last Contact', 'next_contact':'Next Contact', 'comments':'Comments'},
				    'columns':{'name':3, 'contact_frequency':1, 'last_contact':2, 'next_contact':2, 'comments':3}}}



secret = 'elzecreto'



# csv_path = '/Users/amigabledave/kasware100/csv_files/important_people.csv'

ImPe_csv_path = os.path.join(os.path.dirname(__file__), 'csv_files', 'Backup_ImPe.csv')


# --- Regular expressions ---

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
PAGE_RE = r'((?:[a-zA-Z0-9_-]+/?)*)'



# --- URL Handler Relation ---------------------------------------------------------------------------

app = webapp2.WSGIApplication([
							 ('/', Home),
							 ('/signup', Signup),
							 ('/login', Login),
                             ('/logout', Logout),
                             ('/mission', Mission),
                             ('/SetViewer/'+ PAGE_RE, SetViewer),
							 ('/important-people',ImportantPeople),
							 ('/NewKSU', NewKSU),
							 ('/editKSU', EditKSU),
							 ('/effort-report',EffortReport),
							 ('/email',Email),
							 ('/LoadCSV', LoadCSV),
							 ('/csv-backup',CSVBackup),
							 ('/PythonBackup/' + PAGE_RE, PythonBackup)

							 ], debug=True)
