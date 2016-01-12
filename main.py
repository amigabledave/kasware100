#KASware v1.0.0 | Copyright 2016 AmigableDave & Co.

import re, os, webapp2, jinja2, logging, hashlib, random, string, csv, pickle
from datetime import datetime, timedelta
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import mail
from operator import itemgetter


template_dir = os.path.join(os.path.dirname(__file__), 'html_templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

today = datetime.today().toordinal()
tomorrow = today + 1

# --- Datastore Entities ----------------------------------------------------------------------------

class Theory(db.Model):
	username = db.StringProperty(required=True)
	password_hash = db.StringProperty(required=True)
	email = db.StringProperty(required=True)
	KAS1 = db.BlobProperty(required=True)
	KAS3 = db.BlobProperty(required=True)
	ImPe = db.BlobProperty(required=True)
	Hist = db.BlobProperty(required=True)	
	MLog = db.BlobProperty(required=True)
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
		return Theory(username=username, 
					  password_hash=password_hash,
					  email=email,
					  KAS1=new_set_KSU('KAS1'),
					  KAS3=new_set_KSU('KAS3'),
					  ImPe=new_set_KSU('ImPe'),
					  MLog=new_set_MLog(),
					  Hist=new_set_Hist())

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
			MLog = unpack_set(theory.MLog)
			todays_log = MLog[today]
			EndValue = todays_log['EndValue'] 
			SmartEffort = todays_log['SmartEffort']
			DumbBehaviour = todays_log['DumbBehaviour']
			PointlessPain = todays_log['PointlessPain']
			return t.render(theory=theory, EndValue=EndValue, SmartEffort=SmartEffort, DumbBehaviour=DumbBehaviour, PointlessPain=PointlessPain, **kw)		
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
				self.redirect('/TodaysMission')




class Login(Handler):
	def get(self):
		self.print_html('login-form.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		theory = Theory.valid_login(username, password)
		if theory:
			self.login(theory)
			self.redirect('/TodaysMission')
		else:
			message = "Incorrect Username or Password"
			self.print_html('login-form.html', error = message)


class Logout(Handler):
	def get(self):
		self.logout()
		self.redirect('/')




#---Todays Mission Handler --- 

class TodaysMission(Handler):

	def get(self):
		if user_bouncer(self):
			return
		mission = todays_mission(self)
		theory = self.theory
		todays_effort = unpack_set(theory.MLog)[today]['SmartEffort']
		
		if len(mission) > 0:
			message = None
		if len(mission) == 0:
			if int(todays_effort) > 0:
				message = "Mission acomplished!!! Enjoy the rest of your day :)"
			else:	
				message = "Define your what would mean for you to be successful today and start working to acomplish it! :)"

		self.print_html('todays-mission.html', mission=mission, message=message)

	def post(self):
		if user_bouncer(self):
			return
		post_details = get_post_details(self)
		ksu_id = post_details['ksu_id']
		user_action = post_details['action_description']

		if user_action == 'Done':
			self.redirect('/Done?ksu_id=' + ksu_id + '&return_to=/TodaysMission')
		
		elif user_action == 'EditKSU':			
			self.redirect('/EditKSU?ksu_id=' + ksu_id + '&return_to=/TodaysMission')

		elif user_action == 'Push':
			user_Action_Push(self)
			self.redirect('/TodaysMission')


def todays_mission(self):
	theory = self.theory
	KAS1 = unpack_set(theory.KAS1)
	KAS3 = unpack_set(theory.KAS3)
	ksu_sets = [KAS1, KAS3]
	result = []

	for ksu_set in ksu_sets:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]

			if ksu['in_mission']:
				result.append(ksu)

			elif ksu['in_pipeline']:
				if ksu['next_event']:
					if today >= int(ksu['next_event']):
						result.append(ksu)
	return result






#---Pipeline Viewer Handler ---

class Pipeline(Handler):
	def get(self):
		if user_bouncer(self):
			return 
		pipeline = current_pipeline(self)
		pipeline = pretty_dates(pipeline)
		pipeline = hide_invisible(pipeline)
		pipeline = list(pipeline.values())
		self.print_html('pipeline.html', pipeline=pipeline)

	def post(self):
		if user_bouncer(self):
			return
		post_details = get_post_details(self)	
		ksu_id = post_details['ksu_id']
		self.redirect('/EditKSU?ksu_id=' + ksu_id)




def current_pipeline(self):
	theory = self.theory
	ksu_set = unpack_set(theory.KAS3) #need to generalize it to go over all sets
	result = {}
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		if ksu['in_pipeline']:
			result[ksu['id']] = ksu
	return result




#---Set Viewer Handler ---

class SetViewer(Handler):
	def get(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_set = unpack_set(eval('theory.' + set_name))
		set_details = ksu_set['set_details']
		ksu_set = pretty_dates(ksu_set)
		ksu_set = hide_invisible(ksu_set)
		ksu_set = make_ordered_ksu_set_list_for_SetViewer(ksu_set)
		viewer_details = d_Viewer[set_name]
		self.print_html('set-viewer.html', viewer_details=viewer_details, ksu_set=ksu_set)

	def post(self, set_name):
		if user_bouncer(self):
			return
		post_details = get_post_details(self)
		user_action = post_details['action_description']	
		
		if user_action == 'NewKSU':
			self.redirect('/NewKSU/' + set_name)

		else:
			ksu_id = post_details['ksu_id']
			set_name = get_type_from_id(ksu_id)
				
			if user_action == 'EditKSU':			
				self.redirect('/EditKSU?ksu_id=' + ksu_id + '&return_to=/SetViewer/' + set_name)

			elif user_action == 'Done':
				self.redirect('/Done?ksu_id=' + ksu_id + '&return_to=/SetViewer/' + set_name)

			elif user_action == 'Add_To_Mission':
				user_Action_Add_To_Mission(self)
				self.redirect('/SetViewer/' + set_name)





def hide_invisible(ksu_set):
	result = {}
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		if ksu['is_visible']:
			result[ksu['id']] = ksu
	return result



def pretty_dates(ksu_set):
	date_attributes = ['last_event', 'next_event', 'last_contact', 'next_contact']
	for date_attribute in date_attributes:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]
			valid_attributes = list(ksu.keys())
			if date_attribute in valid_attributes:	
				if ksu[date_attribute]:
					date_ordinal = int(ksu[date_attribute])
					pretty_date = unpack_date(date_ordinal)
					ksu['pretty_' + date_attribute] = pretty_date
	return ksu_set
	


def make_ordered_ksu_set_list_for_SetViewer(ksu_set): #xx
	if len(ksu_set) == 0:
		return []

	set_name = get_type_from_id(ksu_set.keys()[0])
	result = []
	set_order = []
	d_view_order_details = {'KAS1':{'attribute':'next_event', 'reverse':False},
							'KAS3':{'attribute':'next_event', 'reverse':False},
							'ImPe':{'attribute':'contact_frequency', 'reverse':False}}

	attribute = d_view_order_details[set_name]['attribute'] 
	reverse = d_view_order_details[set_name]['reverse']

	# number_attributes = ['contact_frequency']
	number_attributes = ['last_event', 'next_event', 'contact_frequency']

	if attribute in number_attributes:	
		for (key, ksu) in ksu_set.items():
			set_order.append((ksu['id'],int(ksu[attribute])))
		set_order = sorted(set_order, key=itemgetter(1), reverse=reverse)	
	else:
		for (key, ksu) in ksu_set.items():
			set_order.append((ksu['id'],ksu[attribute]))
		set_order = sorted(set_order, key=itemgetter(1), reverse=reverse)		

	for e in set_order:
		ksu_id = e[0]
		result.append(ksu_set[ksu_id])

	return result




def pack_date(date_string):
	return datetime.strptime(date_string, '%d-%m-%Y').toordinal()


def unpack_date(date_ordinal):
	return datetime.fromordinal(date_ordinal).strftime('%a, %b %d, %Y')



def not_ugly_dates(ksu_set):
	date_attributes = ['last_event', 'next_event', 'last_contact', 'next_contact']
	for date_attribute in date_attributes:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]
			valid_attributes = list(ksu.keys())
			if date_attribute in valid_attributes:	
				if ksu[date_attribute]:
					number_date = int(ksu[date_attribute])
					pretty_date = datetime.fromordinal(number_date).strftime('%d-%m-%Y')
					ksu[date_attribute] = pretty_date
	return ksu_set








#--- New & Edit KSU Handlers ---

class NewKSU(Handler):
	
	def get(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_set = unpack_set(eval('theory.' + set_name))
		ksu = new_ksu(self, set_name)
		self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name ,title='Create')

	def post(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory	
		post_details = get_post_details(self)
		if post_details['action_description'] == 'Create':
			input_error = user_input_error(post_details)
			if input_error:
				ksu_set = unpack_set(eval('theory.' + set_name))
				ksu = new_ksu(self, set_name)
				ksu = update_ksu_with_post_details(ksu, post_details)
				show_date_as_inputed(ksu, post_details) # Shows the date as it was typed in by the user
				self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name, title='Create', input_error=input_error)
			else:
				user_Action_Create_ksu(self, set_name)
				self.redirect('/SetViewer/' + set_name)






class EditKSU(Handler):
	def get(self):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_id = self.request.get('ksu_id')
		set_name = get_type_from_id(ksu_id)
		ksu_set = unpack_set(eval('theory.' + set_name))
		ksu_set = not_ugly_dates(ksu_set)
		ksu = ksu_set[ksu_id]		
		self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name, title='Edit')

	def post(self):
		if user_bouncer(self):
			return
		theory = self.theory			
		post_details = get_post_details(self)
		set_name = get_type_from_id(post_details['ksu_id'])

		if post_details['action_description'] == 'Save':
			input_error = user_input_error(post_details)

			if input_error:
				ksu_id = post_details['ksu_id']
				set_name = get_type_from_id(ksu_id)
				ksu_set = unpack_set(eval('theory.' + set_name))
				ksu_set = not_ugly_dates(ksu_set)
				ksu = ksu_set[ksu_id]
				ksu = update_ksu_with_post_details(ksu, post_details)			
				show_date_as_inputed(ksu, post_details) # Shows the date as it was typed in by the user
				self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name, title='Edit KSU', input_error=input_error)

			else:
				user_Action_Edit_ksu(self)

		elif post_details['action_description'] == 'Delete':
			user_Action_Delete_ksu(self)

		return_to = self.request.get('return_to')	
		self.redirect(return_to)	




def show_date_as_inputed(ksu, post_details):
	if 'last_event' in post_details:
		ksu['last_event'] = post_details['last_event']
	return



#---Done Handler---

class Done(Handler):
	def get(self):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_id = self.request.get('ksu_id')
		set_name = get_type_from_id(ksu_id)
		ksu_set = unpack_set(eval('theory.' + set_name))
		ksu_set = not_ugly_dates(ksu_set)
		ksu = ksu_set[ksu_id]	
		dropdowns = make_dropdowns(theory)
		self.print_html('done.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name)

	def post(self):
		if user_bouncer(self):
			return
		theory = self.theory	
		post_details = get_post_details(self)
		set_name = get_type_from_id(post_details['ksu_id'])
		EndValue_sets = ['KAS1']
		SmartEffort_sets = ['KAS3']
		
		if post_details['action_description'] == 'Done_Confirm':
			input_error = user_input_error(post_details)

			if input_error:
				ksu_id = post_details['ksu_id']
				set_name = get_type_from_id(ksu_id)
				ksu_set = unpack_set(eval('theory.' + set_name))
				ksu_set = not_ugly_dates(ksu_set)
				ksu = ksu_set[ksu_id]
				ksu['time_cost'] = post_details['duration']
				dropdowns = make_dropdowns(theory)
				self.print_html('done.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name, input_error=input_error)
		
			else:
				if set_name in EndValue_sets:
					user_Action_Done_EndValue(self)
				
				if set_name in SmartEffort_sets:	
					user_Action_Done_SmartEffort(self)
				
				return_to = self.request.get('return_to')
				self.redirect(return_to)



def make_ordered_dropdown_tuples_list_of_ImPe(ImPe): #xx Aqui nos quedamos
	result = [(None,'No one')]
	ImPe = hide_invisible(ImPe)
	ordered_ImPe_list = make_ordered_ksu_set_list_for_SetViewer(ImPe)
	for ksu in ordered_ImPe_list:
		result.append((ksu['id'],ksu['description']))	
	return result


def make_dropdowns(theory):
	ImPe = unpack_set(theory.ImPe)
	dropdowns = {'People': make_ordered_dropdown_tuples_list_of_ImPe(ImPe)}
	return dropdowns


#--- Effort Report Handler --- 

class EffortReport(Handler):
	def get(self):
		if user_bouncer(self):
			return
		theory = self.theory
		report = create_effort_report(theory,today)
		self.print_html('effort-report.html', report=report)



def get_attribute_from_id(ksu_set, ksu_id, ksu_attribute):
	return ksu_set[ksu_id][ksu_attribute]



def create_effort_report(theory, date):
	result = []
	KAS3 = unpack_set(theory.KAS3)
	Hist = unpack_set(theory.Hist)
	for event in Hist:
		event = Hist[event]
		if event['date'] == date and event['type']=='Effort':			
			report_item = {'effort_description':None,'effort_reward':0}
			report_item['effort_description'] = get_attribute_from_id(KAS3, event['ksu_id'], 'description')
			report_item['effort_reward'] = event['value']
			result.append(report_item)
	return result





#--- Development Handlers --------

#--- Load CSV  ---

class LoadCSV(Handler):
	def get(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory
		developer_Action_Load_CSV(theory, set_name)
		self.redirect('/SetViewer/' + set_name)	



#--- Create CSV Backup ---

class CSVBackup(Handler):
	def get(self):
		if user_bouncer(self):
			return
		KAS3 = unpack_set(theory.KAS3)
		output = create_csv_backup(KAS3, ['id','description','frequency','last_event','status'])
		self.write(output)



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
		if user_bouncer(self):
			return
		theory = self.theory	
		ksu_set = unpack_set(eval('theory.' + set_name))
		self.write(ksu_set)







# --- Additional Helper Functions -----------------------------------------------------------------------------

#--- Essentials ---

def user_bouncer(self):
	theory = self.theory
	if theory:
		return False
	else:
		self.redirect('/login')
		return True



def get_post_details(self):
	post_details = {}
	arguments = self.request.arguments()
	for argument in arguments:
		post_details[str(argument)] = self.request.get(str(argument))
	return adjust_post_details(post_details)


def adjust_post_details(post_details): 
	details = {}
	for (attribute, value) in post_details.items():
		if value and value!='' and value!='None':
			details[attribute] = value
	return details


def pack_set(ksu_set):
	return pickle.dumps(ksu_set)


def unpack_set(ksu_pickled_set):
	return pickle.loads(ksu_pickled_set)


def get_digit_from_id(ksu_id):
	return int(ksu_id.split("_")[1])


def get_type_from_id(ksu_id):
	return ksu_id.split("_")[0]





#--- Update Stuff ---

def update_ksu_with_post_details(ksu, details):
	valid_attributes = list(ksu.keys())
	for (attribute, value) in details.items():
		if attribute in valid_attributes:
			ksu[attribute] = value
	return ksu



def update_ksu_next_event(theory, post_details):
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	valid_sets = ['KAS1', 'KAS3']	
	if set_name not in valid_sets:
		return
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	user_action = post_details['action_description']
	
	if user_action == 'Done_Confirm':
		ksu['last_event'] = today
		
		if set_name == 'KAS1':
			ksu['next_event'] = today + int(ksu['charging_time'])

		if set_name == 'KAS3':
			ksu['next_event'] = today + int(ksu['frequency'])

	elif user_action == 'Push':
		ksu['next_event'] = tomorrow

	update_theory(theory, ksu_set)	
	return




def update_ksu_in_mission(theory, post_details):
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	valid_sets = ['KAS1', 'KAS3']	
	if set_name not in valid_sets:
		return

	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]	
	user_action = post_details['action_description']

	if user_action == 'Add_To_Mission':
		ksu['in_mission'] = True

	elif user_action == 'Done_Confirm':
		ksu['in_mission'] = False

	elif user_action == 'Push':
		ksu['in_mission'] = False		

	update_theory(theory, ksu_set)	
	return






def update_MLog(theory, event):
	MLog = unpack_set(theory.MLog)

	date = event['date']
	event_type = event['type']

	if event_type == 'Done':
		event_units = event['units']
		event_value = int(event['value'])
		log = MLog[date]
		log[event_units] = log[event_units] + event_value

	ksu_id = event['ksu_id']
	event_id = event['id']
	if ksu_id in MLog:
		ksu_history = MLog[ksu_id]
		ksu_history.append(event_id)
	else:
		ksu_history = [event_id]
	MLog[ksu_id] = ksu_history

	theory.MLog = pack_set(MLog)
	return


def update_set(ksu_set, ksu):
	ksu_id = ksu['id']
	ksu_set[ksu_id]=ksu
	return


def update_theory(theory, ksu_set):
	set_name = ksu_set['set_details']['set_type']
	if set_name == 'KAS1':
		theory.KAS1 = pack_set(ksu_set)
	if set_name == 'KAS3':
		theory.KAS3 = pack_set(ksu_set)
	if set_name == 'ImPe':
		theory.ImPe = pack_set(ksu_set)
	return






#---Templates---

#General Attributes
i_BASE_KSU = {'id': None,
		      'parent_id': None,
		      'subtype':None,
		      'status':'Active', # ['Active', 'Hold', 'Deleted']
	    	  'description': None,
	    	  'is_visible': True,
		      'is_private': False,
	    	  'target_person':None,
	    	  'local_tags': None, #la idea es que el atributo sea una lista con varios elementos, ahora en esta primera version solo hay espeacio para uno (80/20)
	    	  'global_tags': None, #la idea es que el atributo sea una lista con varios elementos, ahora en esta primera version solo hay espeacio para uno (80/20)
	    	  'comments': None}



#KAS1 Specifics - End Value Base Portforlio - Acciones Recurrentes Proactivas con el objetivo de experimentar valor final
i_KAS1_KSU ={'charging_time':"365",
			 'last_event':None,
			 'next_event':None,
			 'in_mission':False,
			 'in_pipeline':False,
			 'is_critical':False,
			 'related_people':None}  #la idea es que el atributo sea una lista con varios elementos, ahora en esta primera version solo hay espeacio para uno (80/20)



#Resource Generation KAS Specifics
i_ReGen_KAS_KSU = {'importance':"3", # the higher the better. Used to calculate FRP (Future Rewards Points). All KSUs start with a relative importance of 3
	    	       'time_cost': "13", # Reasonable Time Requirements in Minutes
	    	       'element': None,
	    	  	   'in_mission': False,
			       'in_pipeline':False,
			       'is_critical': False}



#KAS3 Specifics	- Resource Generation Base Portfolio - Acciones Recurrentes Proactivas con el objetivo de generar recursos	
i_KAS3_KSU = {'frequency': "7",
			  'best_day': "None",
			  'best_time': None,
			  'any_any':False, # This particular action can be executed at anytime and in anyplace
			  'last_event': None,
			  'next_event': None,
			  'in_pipeline':True} #elengance could be improved since this attribute is also in the base, is here just to overwrite the value



i_KAS4_KSU = {'best_time': None,
			  'target_exe': None,
			  'pipeline':"9"}



i_Wish_KSU = {'nature': None, # End Value or Resoruce -- Names to be improved
			  'exitement_lvl': None,
			  'pipeline': "9"} 



i_ImPe_KSU = {'contact_ksu_id':None,
			  'contact_frequency':"30",
			  'kasware_username':None,
			  'relation_type':None,
			  'last_contact':None,
			  'next_contact':None,
			  'important_since':today,
			  'fun_facts':None,
			  'email':None,
			  'phone':None,
			  'facebook':None,
			  'birthday':None,
			  'related_ksus':[]}



i_BASE_Event = {'id':None,
				'ksu_id':None,
				'date':today,
				'type':None} # Depends on the KSU [Created, Edited ,Deleted]


i_KAS_Event = {'units':None, # EndValue, SmartEffort, and other tipes to be determined
			   'value':None} # Amoount of EndValue or SmartEffort Points Earned



i_KAS1_Event = {'duration':None, # To calculate Amount of EndValue Points Earned
			    'intensity':None, # To calculate Amount of EndValue Points Earned
			    'thanks':None,
			    'comments':None} # Personas que fueron factor importantes en disfrutar de este momento  


i_KAS3_Event = {'duration':None, # To calculate Amount of SmartEffort Points Earned
			    'importance':None, # To calculate Amount of SmartEffort Points Earned
			    'joy':False,
			    'disconfort':False}



template_recipies = {'KAS1_KSU':[i_BASE_KSU, i_KAS1_KSU],
					 'KAS3_KSU':[i_BASE_KSU, i_ReGen_KAS_KSU, i_KAS3_KSU],
					 'ImPe_KSU':[i_BASE_KSU, i_ImPe_KSU],
					 'KAS1_Event':[i_BASE_Event, i_KAS_Event, i_KAS1_Event],
					 'KAS3_Event':[i_BASE_Event, i_KAS_Event, i_KAS3_Event],
					 'ImPe_Event':[i_BASE_Event],
					 'Hist_Event':[i_BASE_Event]}




def make_template(set_name, item_type): # Item type could be KSU or Event
	template = {}
	target_template = set_name + '_' + item_type
	template_recipe = template_recipies[target_template]
	for ingredient in template_recipe:
		for (attribute,value) in ingredient.items():
			template[attribute] = value
	return template




#--- Create new Sets --- 



def new_set_KSU(set_name):
	result = {}
	ksu = make_template(set_name, 'KSU')
	ksu['set_size'] = 0
	ksu['id'] = set_name +'_0'
	ksu['set_type'] = set_name
	ksu['is_visible'] = False
	result['set_details'] = ksu
	return pack_set(result)



def new_set_Hist():
	result = {}
	event = make_template('Hist', 'Event')
	event['id'] = 'Event_0'
	event['type'] = 'Created'
	event['set_type'] = 'Event'
	event['set_size'] = 0
	result['set_details'] = event
	return pack_set(result)



def new_set_MLog(start_date=(735964), end_date=(735964+366)): #start_date = Jan 1, 2016 |  end_date = Dec 31, 2016  
	result = {}
	for date in range(start_date, end_date):
		entry = {'EndValue':0,'SmartEffort':0, 'DumbBehaviour':0, 'PointlessPain':0}
		entry['date'] = datetime.fromordinal(date).strftime('%d-%m-%Y')
		result[date] = entry
	return pack_set(result)




#--- Create new Set Items ---


def new_ksu(self, set_name):
	theory = self.theory
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = make_template(set_name, 'KSU')
	ksu_id = create_id(ksu_set)
	ksu['id'] = ksu_id
	return ksu


def new_event(Hist, set_name):
	event = make_template(set_name, 'Event')
	event_id = create_id(Hist)
	event['id'] = event_id
	return event


def create_id(ksu_set):
	set_details = ksu_set['set_details']
	set_type = set_details['set_type']
	id_digit = int(set_details['set_size']) + 1
	set_details['set_size'] = id_digit
	ksu_id = set_type + '_' + str(id_digit)
	return ksu_id



#--- Add items to sets. IT DOES NOT STORE THEM, IS STILL NECESARY TO ADD THE FUNCTION 	theory.put() ---

def add_Created_event(theory, ksu):
	Hist = unpack_set(theory.Hist)
	ksu_id = ksu['id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, set_name)
	event['type'] = 'Created'
	event['ksu_id'] = ksu_id
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event



def add_Edited_event(theory, ksu):
	Hist = unpack_set(theory.Hist)
	ksu_id = ksu['id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, set_name)
	event['type'] = 'Edited'
	event['ksu_id'] = ksu_id
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event



def add_Deleted_event(theory, ksu):
	Hist = unpack_set(theory.Hist)
	ksu_id = ksu['id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, set_name)
	event['type'] = 'Deleted'
	event['ksu_id'] = ksu_id
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event


def add_SmartEffort_event(theory, post_details): #Duration & Importance to be updated from the post detail given that it could change
	Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, set_name)

	event['ksu_id'] = ksu_id
	event['type'] = 'Done'
	event['units'] = 'SmartEffort'
	event['duration'] = post_details['duration']
	event['importance'] = post_details['importance']
	if 'joy' in post_details:
		event['joy'] = True
	if 'disconfort' in post_details:
		event['disconfort'] = True
	event['value'] = int(post_details['duration'])*(int(post_details['importance']) + event['joy'] + event['disconfort'])

	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event


def add_EndValue_event(theory, post_details): #Duration & Importance to be updated from the post detail given that it could change
	Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, set_name)

	event['ksu_id'] = ksu_id
	event['type'] = 'Done'
	event['units'] = 'EndValue'
	event['duration'] = post_details['duration']
	event['intensity'] = post_details['intensity']
	
	if 'thanks' in post_details:
		event['thanks'] = post_details['thanks']
	if 'comments' in post_details:
		event['comments'] = post_details['comments']

	event['value'] = int(post_details['duration'])*int(post_details['intensity'])

	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event









def add_ksu_to_set(self, set_name):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = make_template(set_name, 'KSU')
	ksu_id = create_id(ksu_set)
	ksu['id'] = ksu_id
	details = prepare_details_for_saving(post_details)
	ksu = update_ksu_with_post_details(ksu, details)
	update_set(ksu_set, ksu)
	update_theory(theory, ksu_set)
	return ksu



def add_edited_ksu_to_set(self): 
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	post_details = prepare_details_for_saving(post_details)
	ksu = update_ksu_with_post_details(ksu, post_details)
	update_set(ksu_set, ksu)
	update_theory(theory, ksu_set)
	return ksu



def add_deleted_ksu_to_set(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	ksu['status'] = 'Deleted'
	ksu['is_visible'] = False
	update_set(ksu_set, ksu)
	update_theory(theory, ksu_set)
	return ksu




def prepare_details_for_saving(post_details):
	checkboxes = ['is_critical', 'is_private', 'in_pipeline']
	details = {'is_critical':False, 'is_private':False, 'in_pipeline':False}
	
	for (attribute, value) in post_details.items():
		
		if attribute in checkboxes:
			details[attribute] = True
		
		elif attribute == 'last_event' or attribute == 'next_event':
			details[attribute] = pack_date(value)

		elif value and value!='' and value!='None':
			details[attribute] = value
	
	return details






#---User Actions ---

def user_Action_Create_ksu(self, set_name):
	theory = self.theory
	ksu = add_ksu_to_set(self, set_name)
	add_Created_event(theory, ksu)
	trigger_additional_actions(self)
	theory.put()
	return


def user_Action_Edit_ksu(self):
	theory = self.theory
	ksu = add_edited_ksu_to_set(self)
	add_Edited_event(theory, ksu)
	trigger_additional_actions(self)
	theory.put()
	return



def user_Action_Delete_ksu(self):
	theory = self.theory
	ksu = add_deleted_ksu_to_set(self)
	add_Deleted_event(theory, ksu)
	trigger_additional_actions(self)
	theory.put()
	return



def user_Action_Done_SmartEffort(self):
	theory = self.theory
	post_details = get_post_details(self)
	update_ksu_next_event(theory, post_details)
	update_ksu_in_mission(theory, post_details)
	add_SmartEffort_event(theory, post_details)
	trigger_additional_actions(self)
	theory.put()
	return



def user_Action_Done_EndValue(self):
	theory = self.theory
	post_details = get_post_details(self)
	update_ksu_next_event(theory, post_details)
	update_ksu_in_mission(theory, post_details)
	add_EndValue_event(theory, post_details)
	trigger_additional_actions(self)
	theory.put()
	return




def user_Action_Push(self):
	theory = self.theory
	post_details = get_post_details(self)
	update_ksu_next_event(theory, post_details)
	update_ksu_in_mission(theory, post_details)
	trigger_additional_actions(self)
	theory.put()
	return


def user_Action_Add_To_Mission(self):
	theory = self.theory
	post_details = get_post_details(self)
	update_ksu_in_mission(theory, post_details)
	trigger_additional_actions(self)
	theory.put()
	return






#--- Additional Actions Triggered by User Actions

def trigger_additional_actions(self):
	theory = self.theory
	post_details = get_post_details(self)
	action_type = post_details['action_description']
	ksu_id = post_details['ksu_id']
	ksu_type = get_type_from_id(ksu_id)
	ksu_set = unpack_set(eval('theory.' + ksu_type))
	ksu_subtype = ksu_set[ksu_id]['subtype']

	if action_type == 'Create':
		
		if ksu_type =='KAS1':
			triggered_Action_create_KAS1_next_event(self)

		if ksu_type == 'KAS3':
			triggered_Action_create_KAS3_next_event(self)
		
		elif ksu_type == 'ImPe':
				triggered_Action_create_ImPe_Contact(self)		

	if action_type == 'Done':
		
		if ksu_subtype == 'ImPe_Contact':
			triggered_Action_Done_ImPe_Contact(self)


	if action_type == 'Delete':
		
		if ksu_type == 'ImPe':
			triggered_Action_delete_ImPe_Contact(self)

	return



def triggered_Action_create_KAS1_next_event(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	KAS1 = unpack_set(theory.KAS1)
	ksu = KAS1[ksu_id]
	if ksu['last_event'] and not ksu['next_event']:
		ksu['next_event'] = int(ksu['last_event']) + int(ksu['charging_time'])
		if ksu['next_event'] < today:
			ksu['next_event'] = today
	elif not ksu['next_event']:
		ksu['next_event'] = today + int(ksu['charging_time'])
	update_set(KAS1, ksu)
	theory.KAS1 = pack_set(KAS1)
	return



def triggered_Action_create_KAS3_next_event(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	KAS3 = unpack_set(theory.KAS3)
	ksu = KAS3[ksu_id]
	if ksu['last_event'] and not ksu['next_event']:
		ksu['next_event'] = int(ksu['last_event']) + int(ksu['frequency'])
		if ksu['next_event'] < today:
			ksu['next_event'] = today
	elif not ksu['next_event']:
		ksu['next_event'] = today
	update_set(KAS3, ksu)
	theory.KAS3 = pack_set(KAS3)
	return


def triggered_Action_create_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	ImPe = unpack_set(theory.ImPe)
	KAS3 = unpack_set(theory.KAS3)
	person = ImPe[ksu_id]
	ksu = make_template('KAS3', 'KSU')
	ksu_id = create_id(KAS3)
	ksu['id'] = ksu_id
	ksu['element'] = 'E500'
	ksu['description'] = 'Contact ' + person['description']
	ksu['frequency'] = person['contact_frequency']
	if person['last_contact']:
		ksu['last_event'] = person['last_contact']
		ksu['next_event'] = int(person['last_contact']) + int(person['contact_frequency'])
	else:
		ksu['next_event'] = today
	person['next_contact'] = ksu['next_event']	
	ksu['time_cost'] = 3
	ksu['target_person'] = person['id']
	ksu['parent_id'] = person['id']
	ksu['subtype'] = 'ImPe_Contact'
	person['contact_ksu_id'] = ksu['id']
	update_set(KAS3, ksu)
	update_set(ImPe, person)
	theory.KAS3 = pack_set(KAS3)
	theory.ImPe = pack_set(ImPe)
	add_Created_event(theory, ksu)
	return ksu



def triggered_Action_delete_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	person_id = post_details['ksu_id']
	ImPe = unpack_set(theory.ImPe)
	KAS3 = unpack_set(theory.KAS3)
	person = ImPe[person_id]
	ksu_id = person['contact_ksu_id']
	ksu = KAS3[ksu_id]
	ksu['status'] = 'Deleted'
	ksu['is_visible'] = False
	update_set(KAS3, ksu)
	theory.KAS3 = pack_set(KAS3)
	add_Deleted_event(theory, ksu)
	return




def triggered_Action_Done_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	KAS3 = unpack_set(theory.KAS3)
	ksu = KAS3[ksu_id]
	person_id = ksu['target_person']
	ImPe = unpack_set(theory.ImPe)
	person = ImPe[person_id]
	person['last_contact'] = ksu['last_event']
	person['next_contact'] = ksu['next_event']
	theory.ImPe = pack_set(ImPe)

	MLog = unpack_set(theory.MLog)
	ksu_history = MLog[ksu_id]
	last_event = ksu_history.pop()
	ksu_history = ksu_history.append(last_event)
	person_history = MLog[person_id]
	person_history.append(last_event)
	MLog[person_id] = person_history
	theory.MLog = pack_set(MLog)
	return





#--- Developer Actions ---


def developer_Action_Load_CSV(theory, set_name):
	csv_path = create_csv_path(set_name)
	standard_sets = [] 

	if set_name in standard_sets:
		developer_Action_Load_Set_CSV(theory, set_name, csv_path)

	elif set_name == 'KAS1':
		developer_Action_Load_KAS1_CSV(theory, csv_path)

	elif set_name == 'KAS3':
		developer_Action_Load_KAS3_CSV(theory, csv_path)		

	elif set_name == 'ImPe':
		developer_Action_Load_ImPe_CSV(theory, csv_path)
	return


def developer_Action_Load_Set_CSV(theory, set_name, csv_path):
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
		ksu_details = digested_ksu
		add_ksu_to_set_from_csv(theory, ksu_details, set_name)		
	theory.put()
	return


def developer_Action_Load_KAS1_CSV(theory, csv_path):
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

		ksu_details = digested_ksu
		ksu = add_ksu_to_set_from_csv(theory, ksu_details, 'KAS1')
		csv_triggered_Action_create_KAS1_next_event(theory, ksu)
	theory.put()


def developer_Action_Load_KAS3_CSV(theory, csv_path):
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

		ksu_details = digested_ksu
		ksu = add_ksu_to_set_from_csv(theory, ksu_details, 'KAS3')
		csv_triggered_Action_create_KAS3_next_event(theory, ksu)
	theory.put()


def developer_Action_Load_ImPe_CSV(theory, csv_path):
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

		ksu_details = digested_ksu
		person = add_ksu_to_set_from_csv(theory, ksu_details, 'ImPe')
		csv_triggered_Action_create_ImPe_Contact(theory, person)
		
	theory.put()
	return 


def create_csv_path(set_name):
	file_name = 'Backup_' + set_name + '.csv'
	return os.path.join(os.path.dirname(__file__), 'csv_files', file_name)


def add_ksu_to_set_from_csv(theory, ksu_details, set_name):
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = make_template(set_name, 'KSU')
	ksu_id = create_id(ksu_set)
	ksu['id'] = ksu_id
	details = prepare_csv_details_for_saving(ksu_details)
	ksu = update_ksu_with_csv_details(ksu, details)	
	update_set(ksu_set, ksu)
	update_theory(theory, ksu_set)
	add_Created_event(theory, ksu)
	return ksu


def update_ksu_with_csv_details(ksu, details):
	for (attribute, value) in details.items():
		ksu[attribute] = value
	return ksu



def csv_triggered_Action_create_KAS1_next_event(theory, ksu):
	KAS1 = unpack_set(theory.KAS1)
	if ksu['last_event'] and not ksu['next_event']:
		ksu['next_event'] = int(ksu['last_event']) + int(ksu['charging_time'])
		if ksu['next_event'] < today:
			ksu['next_event'] = today
	elif not ksu['next_event']:
		ksu['next_event'] = today + int(ksu['charging_time'])
	update_set(KAS1, ksu)
	theory.KAS1 = pack_set(KAS1)
	return



def csv_triggered_Action_create_KAS3_next_event(theory, ksu):
	KAS3 = unpack_set(theory.KAS3)
	if ksu['last_event'] and not ksu['next_event']:
		ksu['next_event'] = int(ksu['last_event']) + int(ksu['frequency'])
		if ksu['next_event'] < today:
			ksu['next_event'] = today
	elif not ksu['next_event']:
		ksu['next_event'] = today
	update_set(KAS3, ksu)
	theory.KAS3 = pack_set(KAS3)
	return




def csv_triggered_Action_create_ImPe_Contact(theory, person):
	ImPe = unpack_set(theory.ImPe)
	KAS3 = unpack_set(theory.KAS3)
	ksu = make_template('KAS3', 'KSU')
	ksu_id = create_id(KAS3)
	ksu['id'] = ksu_id
	ksu['element'] = 'E500'
	ksu['description'] = 'Contact ' + person['description']
	ksu['frequency'] = person['contact_frequency']
	if person['last_contact']:
		ksu['last_event'] = person['last_contact']
		ksu['next_event'] = int(person['last_contact']) + int(person['contact_frequency'])
	else:
		ksu['next_event'] = today
	person['next_contact'] = ksu['next_event'] 	
	ksu['time_cost'] = 3
	ksu['target_person'] = person['id']
	ksu['parent_id'] = person['id']
	ksu['subtype'] = 'ImPe_Contact'
	person['contact_ksu_id'] = ksu['id']
	update_set(KAS3, ksu)
	update_set(ImPe, person)
	theory.KAS3 = pack_set(KAS3)
	theory.ImPe = pack_set(ImPe)
	add_Created_event(theory, ksu)
	return ksu




#--- CSV Helper Functions



def prepare_csv_details_for_saving(post_details):
	details = {}
	checkboxes = ['is_critical', 'is_private']
	for (attribute, value) in post_details.items():
		if attribute in checkboxes:
			details[attribute] = True
		elif attribute == 'last_event':
			if valid_csv_date(value):
				details[attribute] = value
		elif value and value!='' and value!='None':
			details[attribute] = value
	return details



def valid_csv_date(dateordinal):
    try:
        datetime.fromordinal(int(dateordinal))
        return True
    except ValueError:
        return False






#--- Validation and Security Functions ---

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



def valid_date(date_string):
    try:
        pack_date(date_string)
        return True
    except ValueError:
        return False



def user_input_error(post_details):
	for (attribute, value) in post_details.items():
		user_error = input_error(attribute, value)
		if user_error:
			return user_error
	return None



def input_error(target_attribute, user_input):
	
	validation_attributes = ['username', 'password', 'description', 'frequency', 'duration', 'last_event', 'next_event', 'comments']

	if target_attribute not in validation_attributes:
		return None
	error_key = target_attribute + '_error' 
		
	if target_attribute == 'last_event' or target_attribute == 'next_event':
		if valid_date(user_input):
			return None
		else:
			return d_RE[error_key]

	if d_RE[target_attribute].match(user_input):
		return None
	else:
		return d_RE[error_key]



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

		'duration': re.compile(r"^[0-9]{1,3}$"),
		'duration_error': 'Duration should be an integer with maximum 3 digits',

		'last_event_error':'Last event format must be DD-MM-YYYY',

		'comments': re.compile(r"^.{0,200}$"),
		'comments_error': 'Comments cannot excede 200 characters'}






#---Global Variables ------------------------------------------------------------------------------




l_Fibonacci = ['1','2','3','5','8','13','21','34','55','89','144']

d_Elements = {'E100': '1. Inner Peace & Consciousness',
			  'E200': '2. Fun & Excitement', 
			  'E300': '3. Meaning & Direction', 
			  'E400': '4. Health & Vitality', 
			  'E500': '5. Love & Friendship', 
			  'E600': '6. Knowledge & Skills', 
			  'E700': '7. Outer Order & Peace', 
			  'E800': '8. Stuff',
		 	  'E900': '9. Money & Power'}


l_Elements = sorted(d_Elements.items())


d_Days = {'None':'None',
		  '1':'1. Sunday',
		  '2':'2. Monday',
		  '3':'3. Tuesday',
		  '4':'4. Wednesday',
		  '5':'5. Thursday',
		  '6':'6. Friday',
		  '7':'7. Saturday'}

l_Days = sorted(d_Days.items())



constants = {'l_Fibonacci':l_Fibonacci,
			 'l_Elements':l_Elements,
			 'l_Days':l_Days,}



d_Viewer ={'KAS1':{'set_title':'End Value Base Portfolio  (KAS1)',
				   'set_name':'KAS1',
				   'attributes':['description','pretty_next_event','pretty_last_event'],
				   'fields':{'description':'Description','pretty_last_event':'Last Event','pretty_next_event':'Fully Charged'},
				   'columns':{'description':5,'pretty_last_event':2,'pretty_next_event':2},
				   'show_Button_Done':True,
				   'show_Button_Add_To_Mission':True},

			'KAS3':{'set_title':'Resource Generation Base Portfolio  (KAS3)',
				    'set_name':'KAS3',
				    'attributes':['description','frequency','importance','pretty_next_event'],
				    'fields':{'description':'Description','frequency':'Frequency','importance':'Rel. Imp.', 'pretty_next_event':'Next Event'},
				    'columns':{'description':5,'frequency':1,'importance':1,'pretty_next_event':2},
				    'show_Button_Done':True,
				   'show_Button_Add_To_Mission':True},
		   
		   'ImPe': {'set_title':'My Important People',
		   			'set_name':'ImPe',
					'attributes':['description', 'contact_frequency', 'pretty_last_contact', 'pretty_next_contact', 'comments'],
				    'fields':{'description':'Name', 'contact_frequency':'C. Freq.', 'pretty_last_contact':'Last Contact', 'pretty_next_contact':'Next Contact', 'comments':'Comments'},
				    'columns':{'description':3, 'contact_frequency':1, 'pretty_last_contact':2, 'pretty_next_contact':2, 'comments':3},
				    'show_Button_Done':False,
				    'show_Button_Add_To_Mission':False}}


secret = 'elzecreto'



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
                             ('/TodaysMission', TodaysMission),
                             ('/Pipeline', Pipeline),
                             ('/SetViewer/' + PAGE_RE, SetViewer),
							 ('/NewKSU/' + PAGE_RE, NewKSU),
							 ('/EditKSU', EditKSU),
							 ('/Done', Done),
							 ('/effort-report',EffortReport),
							 ('/email',Email),
							 ('/LoadCSV/' + PAGE_RE, LoadCSV),
							 ('/csv-backup',CSVBackup),
							 ('/PythonBackup/' + PAGE_RE, PythonBackup)
							 ], debug=True)
