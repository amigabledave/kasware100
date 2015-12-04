#KASware v1.0.0 | Copyright 2015 AmigableDave & Co.

import re, os, webapp2, jinja2, logging, hashlib, random, string
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
			return t.render(theory=theory, **kw)
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
		details = dict(frequency=frequency, x_person_name=name)
		add_important_person_to_theory(theory, details)
		self.redirect('/important-people')


class Mission(Handler):

	def get(self):
		theory = self.theory
		mission = todays_mission(theory)
		self.print_html('todays-mission.html', mission=mission)

	def post(self):
		theory = self.theory
		ksu_set = eval(theory.kas1)
		target_ksu = int(self.request.get('ksu_id_digit'))
		ksu = ksu_set[target_ksu]
		event_comments = self.request.get('event_comments')
		done(ksu, event_comments)
		theory.kas1 = str(ksu_set)
		theory.put()
		self.redirect('/mission')
		# arguments = self.request.arguments()
		# result = []
		# for e in arguments:
		# 	result.append(self.request.get(e))
		# self.response.out.write(str(result)+str(arguments))


class Email(Handler):
    def get(self):
    	mail.send_mail(sender="<mission@kasware100.appspotmail.com>", to="Dave <amigabledave@gmail.com>", subject="Test email", body="Hello Dave! This was sent from your appengine")
    	self.response.write('Email sent!')


def done(ksu, event_comments=None):
	event = new_event()
	event['event_date'] = today
	event['event_type'] = 'Done'
	event['event_comments'] =event_comments
	history = ksu['history']
	history.append(event)
	ksu['history'] = history
	frequency = int(ksu['frequency'])
	next_exe = today + frequency
	ksu['next_exe'] = next_exe
	ksu['lastest_exe'] = today
	return



# --- Datastore Entities ----------------------------------------------------------------------------

class Theory(db.Model):
	username = db.StringProperty(required=True)
	password_hash = db.StringProperty(required=True)
	email = db.StringProperty(required=True)
	kas1 = db.TextProperty(required=True)
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
		return Theory(username=username, password_hash=password_hash, email=email, kas1=new_kas1)

	@classmethod
	def valid_login(cls, username, password):
		theory = cls.get_by_username(username)
		if theory and validate_password(username, password, theory.password_hash):
			return theory




# --- Helper Functions -----------------------------------------------------------------------------

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

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
			   'is_critical': False,
			   'comments': None,
			   'lastest_exe':None, 
			   'next_exe':None,
			   'target_exe':None,
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
			   'event_hpts':0,
			   'event_epts':0,
			   'event_spts':0}
	return event





def add_important_person_to_theory(theory, details):
	ksu_set = eval(theory.kas1)
	ksu = new_ksu(ksu_set)
	ksu['ksu_subtype'] = 'Important_Person'
	ksu['element'] = '4_Love_Friendship'
	ksu['description'] = 'Contactar a ' + details['x_person_name']
	ksu['next_exe'] = today + int(details['frequency'])
	for key, value in details.iteritems():
		ksu[key] = value
	ksu_set.append(ksu)
	theory.kas1 = str(ksu_set)
	theory.put()
	return


def todays_mission(theory):
	ksu_set = eval(theory.kas1)
	result = []
	for ksu in ksu_set:
		if ksu['next_exe']:
			delay = today - ksu['next_exe']
			status = ksu['status']
			if delay >= 0 and status=='Active':
				result.append(ksu)
	return result


def my_important_people(theory):
	kas1 = eval(theory.kas1)
	result = []
	for ksu in kas1:
		if ksu['ksu_subtype'] == 'Important_Person':
			result.append(ksu)
	return result




# --- Global Variables ------------------------------------------------------------------------------

list_elements_cat = ['1. Fun & Excitement', 
					 '2. Meaning & Direction', 
					 '3. Health & Vitality', 
					 '4. Love & Friendship', 
					 '5. Knowledge & Skills', 
					 '6. Outer Peace', 
					 '7. Money & Resources', 
					 '8. Inner Peace']

secret = 'elzecreto'

today = datetime.today().toordinal() + 100

new_kas1 = "[{'ksu_type': 'kas1', 'ksu_subtype': None, 'next_exe':None, 'imp_person_name':None}]"

# --- URL Handler Relation ---------------------------------------------------------------------------

app = webapp2.WSGIApplication([
							 ('/', Home),
							 ('/signup', Signup),
							 ('/login', Login),
                             ('/logout', Logout),
                             ('/mission', Mission),
							 ('/important-people',ImportantPeople),
							 ('/email',Email)
							 ], debug=True)
