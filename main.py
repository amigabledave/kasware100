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
	KAS2 = db.BlobProperty(required=True)	
	KAS3 = db.BlobProperty(required=True)
	KAS4 = db.BlobProperty(required=True)

	BigO = db.BlobProperty(required=True)
	BOKA = db.BlobProperty(required=True)
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
					  KAS2=new_set_KSU('KAS2'),					  
					  KAS3=new_set_KSU('KAS3'),
					  KAS4=new_set_KSU('KAS4'),
					 
					  BigO=new_set_KSU('BigO'),
					  BOKA=new_set_KSU('BOKA'),
					  ImPe=new_set_KSU('ImPe'),
					 
					  Hist=new_set_Hist(),
					  MLog=new_set_MLog())

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
			Stupidity = todays_log['Stupidity']
			return t.render(theory=theory, EndValue=EndValue, SmartEffort=SmartEffort, Stupidity=Stupidity, **kw)		
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
	KAS2 = unpack_set(theory.KAS2)
	BOKA = unpack_set(theory.BOKA)

	ksu_sets = [KAS1, KAS2, BOKA]
	result = []

	for ksu_set in ksu_sets:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]

			if ksu['in_mission']:
				result.append(ksu)

			elif ksu['in_upcoming']:
				if ksu['next_event']:
					if today >= int(ksu['next_event']):
						result.append(ksu)
	return result






#---Upcoming Viewer Handler ---

class Upcoming(Handler):
	def get(self):
		if user_bouncer(self):
			return 
		upcoming = current_upcoming(self)
		upcoming = pretty_dates(upcoming)
		upcoming = hide_invisible(upcoming)
		upcoming = make_ordered_ksu_set_list_for_upcoming(upcoming)
		view_groups = define_upcoming_view_groups(upcoming)
		self.print_html('upcoming.html', upcoming=upcoming, view_groups=view_groups)

	def post(self):
		if user_bouncer(self):
			return			
		post_details = get_post_details(self)
		user_action = post_details['action_description']

		if user_action == 'Add_To_Mission':
			user_Action_Add_To_Mission(self)
			self.redirect('/Upcoming')

		if user_action == 'EditKSU':
			ksu_id = post_details['ksu_id']
			self.redirect('/EditKSU?ksu_id=' + ksu_id + '&return_to=/Upcoming')




def current_upcoming(self):

	theory = self.theory
	KAS1 = unpack_set(theory.KAS1)
	KAS2 = unpack_set(theory.KAS2)
	BOKA = unpack_set(theory.BOKA)
	ksu_sets = [KAS1, KAS2, BOKA]
	result = {}

	for ksu_set in ksu_sets:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]
			if ksu['in_upcoming']:
				result[ksu['id']] = ksu

	return result



def make_ordered_ksu_set_list_for_upcoming(current_upcoming): 
	ksu_set = current_upcoming 

	if len(ksu_set) == 0:
		return []
	result = []
	set_order = []

	attribute = 'next_event'
	reverse = False

	for (key, ksu) in ksu_set.items():
		set_order.append((ksu['id'],int(ksu[attribute])))
	set_order = sorted(set_order, key=itemgetter(1), reverse=reverse)	

	for e in set_order:
		ksu_id = e[0]
		ksu = ksu_set[ksu_id]
		ksu['view_group'] = define_ksu_upcoming_group(int(ksu['next_event']))
		result.append(ksu_set[ksu_id])

	return result




def define_ksu_upcoming_group(date_ordinal):
	date = datetime.fromordinal(date_ordinal)
	date_month = date.strftime('%B')
	date_year = date.strftime('%Y')
	date = datetime.toordinal(date)

	today = datetime.today().toordinal()
	tomorrow = today + 1

	if date <= today:
		group = 'Today'

	elif date == tomorrow:
		group = 'Tomorrow'

	elif today + 7 >= date:
		group = 'This Week'

	elif today + 30 >= date:
		group = 'This Month'

	else:
		group = date_month + ' ' + date_year

	return group

def define_upcoming_view_groups(ordered_upcoming_list):
	upcoming = ordered_upcoming_list
	groups = []
	for ksu in upcoming:
		group = ksu['view_group']
		if group not in groups:
			groups.append(group)
	return groups




#---Set Viewer Handler ---

class SetViewer(Handler):
	def get(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_set = unpack_set(eval('theory.' + set_name))
		set_details = ksu_set['set_details']
		ksu_set = pretty_dates(ksu_set)
		
		if set_name != 'Hist':
			ksu_set = hide_invisible(ksu_set)
		ksu_set = make_ordered_ksu_set_list_for_SetViewer(ksu_set)

		viewer_details = d_Viewer[set_name]
		if viewer_details['grouping_attribute'] == 'local_tags':
			viewer_details['grouping_list'] = make_local_tags_grouping_list(ksu_set)

		self.print_html('set-viewer.html', viewer_details=viewer_details, ksu_set=ksu_set)

	def post(self, set_name):
		if user_bouncer(self):
			return
		post_details = get_post_details(self)
		user_action = post_details['action_description']	
		
		if user_action == 'NewKSU':
			self.redirect('/NewKSU/' + set_name + '?return_to=/SetViewer/' + set_name)

		else:
			ksu_id = post_details['ksu_id']
			set_name = get_type_from_id(ksu_id)
				
			if user_action == 'EditKSU':			
				self.redirect('/EditKSU?ksu_id=' + ksu_id + '&return_to=/SetViewer/' + set_name)

			if user_action == 'Done':
				self.redirect('/Done?ksu_id=' + ksu_id + '&return_to=/SetViewer/' + set_name)

			if user_action == 'Fail':
				self.redirect('/Failure?ksu_id=' + ksu_id + '&return_to=/SetViewer/' + set_name)

			if user_action == 'Add_To_Mission':
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
	


def make_ordered_ksu_set_list_for_SetViewer(ksu_set):
	if len(ksu_set) == 0:
		return []

	set_name = get_type_from_id(ksu_set.keys()[0])

	if set_name == 'Event':
		set_name = 'Hist'

	result = []
	set_order = []
	d_view_order_details = {'KAS1':{'attribute':'next_event', 'reverse':False},
							'KAS2':{'attribute':'next_event', 'reverse':False},	
							'KAS3':{'attribute':'importance', 'reverse':False},
							'KAS4':{'attribute':'importance', 'reverse':False},

							'BigO':{'attribute':'target_date', 'reverse':False},
							'BOKA':{'attribute':'priority', 'reverse':False},

							'ImPe':{'attribute':'contact_frequency', 'reverse':False},
							'Hist':{'attribute':'date', 'reverse':False}}

	attribute = d_view_order_details[set_name]['attribute'] 
	reverse = d_view_order_details[set_name]['reverse']

	# number_attributes = ['contact_frequency']
	number_attributes = ['last_event', 'next_event', 'contact_frequency', 'target_date']

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



def not_ugly_dates(ksu):
	valid_attributes = list(ksu.keys())
	for date_attribute in date_attributes:
		if date_attribute in valid_attributes:	
			if ksu[date_attribute]:
				number_date = int(ksu[date_attribute])
				not_ugly_date = datetime.fromordinal(number_date).strftime('%d-%m-%Y')
				ksu[date_attribute] = not_ugly_date
	return ksu



def make_local_tags_grouping_list(ksu_set):
	result = []
	local_tags = []
	for ksu in ksu_set:
		tag = ksu['local_tags'] 
		if tag not in local_tags and tag != None:
			local_tags.append(tag)
			result.append((tag,tag))
	result = sorted(result)
	result.append((None, 'Other'))
	return result




#---Big Os Viwer Handler --

class BigOViewer(Handler):
	def get(self):
		if user_bouncer(self):
			return
		theory = self.theory
		
		BigO = unpack_set(theory.BigO)	
		BigO = hide_invisible(BigO)
		BigO = pretty_dates(BigO)
		BigO = add_days_left(BigO)
		BigO = make_ordered_ksu_set_list_for_SetViewer(BigO)

		BOKA = unpack_set(theory.BOKA)
		BOKA = hide_invisible(BOKA)
		BOKA = make_ordered_ksu_set_list_for_SetViewer(BOKA)
	
		self.print_html('BigOViewer.html', BigO=BigO, BOKA=BOKA, today=today ) #viewer_details=viewer_details


	def post(self):
		if user_bouncer(self):
			return
		post_details = get_post_details(self)
		user_action = post_details['action_description']
	
		
		if user_action == 'NewKSU':
			self.redirect('/NewKSU/BigO?return_to=/BigOViewer')


		elif user_action == 'Add_Child_KSU':
			parent_id = post_details['ksu_id']
			self.redirect('/NewKSU/BOKA?return_to=/BigOViewer&parent_id=' + parent_id)
		

		else:
			ksu_id = post_details['ksu_id']
			set_name = get_type_from_id(ksu_id)
				
			if user_action == 'EditKSU':			
				self.redirect('/EditKSU?ksu_id=' + ksu_id + '&return_to=/BigOViewer')

			if user_action == 'Done':
				self.redirect('/Done?ksu_id=' + ksu_id + '&return_to=/BigOViewer')

			if user_action == 'Fail':
				self.redirect('/Failure?ksu_id=' + ksu_id + '&return_to=/BigOViewer')

			if user_action == 'Add_To_Mission':
				user_Action_Add_To_Mission(self)
				self.redirect('/BigOViewer')





def add_days_left(ksu_set):
	for date_attribute in date_attributes:
		for ksu in ksu_set:
			ksu = ksu_set[ksu]
			valid_attributes = list(ksu.keys())
			if date_attribute in valid_attributes:	
				if ksu[date_attribute]:
					date_ordinal = int(ksu[date_attribute])
					days_left = date_ordinal - today
					ksu['days_left_to_' + date_attribute] = str(days_left)
	return ksu_set







#---New KSU Handler ---

class NewKSU(Handler):
	
	def get(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_set = unpack_set(eval('theory.' + set_name))	
		ksu = new_ksu(self, set_name)
		ksu = not_ugly_dates(ksu)

		parent_id = self.request.get('parent_id')
		if parent_id:
			if set_name == 'BOKA':
				ksu['parent_id'] = parent_id
			else:
				parent = ksu_set[parent_id]
				update_child_with_parent(ksu, parent)
		
		self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name ,title='Create')

	def post(self, set_name):
		if user_bouncer(self):
			return
		theory = self.theory	
		post_details = get_post_details(self)
		return_to = self.request.get('return_to')
		user_action = post_details['action_description']

		if user_action == 'Create':
			input_error = user_input_error(post_details)
			if input_error:
				ksu_set = unpack_set(eval('theory.' + set_name))
				ksu = new_ksu(self, set_name)
				ksu = update_ksu_with_post_details(ksu, post_details)
				show_date_as_inputed(ksu, post_details) # Shows the date as it was typed in by the user
				self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name, title='Create', input_error=input_error)
			else:
				user_Action_Create_ksu(self, set_name)
				self.redirect(return_to)

		if user_action == 'Discard':
			self.redirect(return_to)


def update_child_with_parent(child_ksu, parent_ksu):
	inheritable_attributes = ['description','project','importance','time_cost','local_tags','in_mission','is_critical','comments','value_type']
	child_attributes = list(child_ksu.keys())
	parent_attributes = list(parent_ksu.keys())
	for attribute in inheritable_attributes:
		if attribute in child_attributes and attribute in parent_attributes:
			child_ksu[attribute] = parent_ksu[attribute]
	child_ksu['parent_id'] = parent_ksu['id']
	return child_ksu





#---Edit KSU Handler ---

class EditKSU(Handler):
	def get(self):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_id = self.request.get('ksu_id')
		set_name = get_type_from_id(ksu_id)
		ksu_set = unpack_set(eval('theory.' + set_name))
		ksu = ksu_set[ksu_id]		
		ksu = not_ugly_dates(ksu)
		self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name, title='Edit')

	def post(self):
		if user_bouncer(self):
			return
		theory = self.theory			
		post_details = get_post_details(self)
		set_name = get_type_from_id(post_details['ksu_id'])
		return_to = self.request.get('return_to')
		user_action = post_details['action_description']

		if user_action == 'Save':
			input_error = user_input_error(post_details)

			if input_error:
				ksu_id = post_details['ksu_id']
				set_name = get_type_from_id(ksu_id)
				ksu_set = unpack_set(eval('theory.' + set_name))
				ksu = ksu_set[ksu_id]
				ksu = update_ksu_with_post_details(ksu, post_details)			
				show_date_as_inputed(ksu, post_details) # Shows the date as it was typed in by the user
				self.print_html('ksu-new-edit-form.html', constants=constants, ksu=ksu, set_name=set_name, title='Edit', input_error=input_error)

			else:
				user_Action_Edit_ksu(self)
				self.redirect(return_to)


		if user_action == 'Discard':
			self.redirect(return_to)


		if user_action == 'Delete':
			user_Action_Delete_ksu(self)
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
		

		if set_name == 'BigO' or set_name == 'Wish':
			event_type = 'Achievement' 
		else:
			if ksu['value_type'] == 'V000':
				event_type = 'EndValue'
			else:
				event_type = 'SmartEffort'

		
		self.print_html('done.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name, event_type=event_type)


	def post(self):
		if user_bouncer(self):
			return
		theory = self.theory	
		post_details = get_post_details(self)
		return_to = self.request.get('return_to')
		user_action = post_details['action_description']
		set_name = get_type_from_id(post_details['ksu_id'])
		ksu_id = post_details['ksu_id']
		set_name = get_type_from_id(ksu_id)
		ksu_set = unpack_set(eval('theory.' + set_name))
		ksu = ksu_set[ksu_id]

		if ksu['value_type'] == 'V000':
			event_type = 'EndValue'
		else:
			event_type = 'SmartEffort'

		
		if user_action == 'Done_Confirm':
			input_error = user_input_error(post_details)

			if input_error:
				ksu['time_cost'] = post_details['duration']
				dropdowns = make_dropdowns(theory)

				self.print_html('done.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name, event_type=event_type, input_error=input_error)
		
			elif event_type == 'EndValue':
				user_Action_Done_EndValue(self)
				self.redirect(return_to)
				
			elif event_type == 'SmartEffort':
				user_Action_Done_SmartEffort(self)
				self.redirect(return_to)

		elif user_action =='Done_Confirm_Continue':
			input_error = user_input_error(post_details)
			parent_id = ksu['id']

			if input_error:
				ksu['time_cost'] = post_details['duration']
				dropdowns = make_dropdowns(theory)

				self.print_html('done.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name, event_type=event_type, input_error=input_error)
		
			elif event_type == 'EndValue':
				user_Action_Done_EndValue(self)
				self.redirect('/NewKSU/' + set_name + '?return_to=' + return_to + '&parent_id=' + parent_id)

				
			elif event_type == 'SmartEffort':
				user_Action_Done_SmartEffort(self)
				self.redirect('/NewKSU/' + set_name + '?return_to=' + return_to + '&parent_id=' + parent_id)


		elif user_action == 'Achieved_Confirm':
			user_Action_Done_Achievement(self)
			self.redirect(return_to)


		elif user_action == 'Discard':
			self.redirect(return_to)	

				



def make_ordered_dropdown_tuples_list_of_ImPe(ImPe):
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




#--- Failure Handler ---

class Failure(Handler):
	def get(self):
		if user_bouncer(self):
			return
		theory = self.theory
		ksu_id = self.request.get('ksu_id')
		set_name = get_type_from_id(ksu_id)
		ksu_set = unpack_set(eval('theory.' + set_name))
		# ksu_set = not_ugly_dates(ksu_set) #no need right now, to be deleted latter if no use
		ksu = ksu_set[ksu_id]	
		dropdowns = make_dropdowns(theory) #no need right now, to be deleted latter if no use
		self.print_html('failure.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name)

	def post(self):
		if user_bouncer(self):
			return
		theory = self.theory	
		post_details = get_post_details(self)
		set_name = get_type_from_id(post_details['ksu_id'])
		Stupidity_sets = ['KAS3', 'KAS4']
		
		if post_details['action_description'] == 'Fail_Confirm':
			if set_name in Stupidity_sets:
				user_Action_Fail_Stupidity(self)
				return_to = self.request.get('return_to')
				self.redirect(return_to)

			# input_error = user_input_error(post_details)  #To be deleted if there is no use for input validation
			# if input_error:
			# 	ksu_id = post_details['ksu_id']
			# 	set_name = get_type_from_id(ksu_id)
			# 	ksu_set = unpack_set(eval('theory.' + set_name))
			# 	ksu_set = not_ugly_dates(ksu_set)
			# 	ksu = ksu_set[ksu_id]
			# 	ksu['time_cost'] = post_details['duration']
			# 	dropdowns = make_dropdowns(theory)
			# 	self.print_html('failure.html', constants=constants, dropdowns=dropdowns, ksu=ksu, set_name=set_name, input_error=input_error)
		
			# else:
			# 	if set_name in Stupidity_sets:
			# 		user_Action_Fail_Stupidity(self)
				
			# 	return_to = self.request.get('return_to')
			# 	self.redirect(return_to)









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
	KAS1 = unpack_set(theory.KAS1)
	Hist = unpack_set(theory.Hist)
	for event in Hist:
		event = Hist[event]
		if event['date'] == date and event['type']=='Effort':			
			report_item = {'effort_description':None,'effort_reward':0}
			report_item['effort_description'] = get_attribute_from_id(KAS1, event['ksu_id'], 'description')
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
		if set_name == 'All':
			self.redirect('/TodaysMission')
		else:
			self.redirect('/SetViewer/' + set_name)	



#--- Create CSV Backup ---

class CSVBackup(Handler):
	def get(self):
		if user_bouncer(self):
			return
		KAS1 = unpack_set(theory.KAS1)
		output = create_csv_backup(KAS1, ['id','description','charging_time','last_event','status'])
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
	valid_sets = ['KAS1', 'KAS2', 'BOKA']	
	if set_name not in valid_sets:
		return

	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	user_action = post_details['action_description']
	
	if user_action == 'Done_Confirm':
		ksu['last_event'] = today
		
		if set_name == 'KAS1':
			ksu['next_event'] = today + int(ksu['charging_time'])

		elif set_name == 'KAS2':
			ksu['next_event'] = None

		elif set_name == 'BOKA':
			ksu['next_event'] = None


			
	elif user_action == 'Push':
		ksu['next_event'] = tomorrow

	update_theory(theory, ksu_set)	
	return




def update_ksu_streak_and_record(theory, post_details):
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	valid_sets = ['KAS3', 'KAS4']	
	if set_name not in valid_sets:
		return

	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	user_action = post_details['action_description']

	if user_action == 'Done_Confirm':

		ksu['streak'] = int(ksu['streak']) + 1
		if int(ksu['streak']) > int(ksu['record']):
			ksu['record'] = ksu['streak']

		if not ksu['success_since']:
			ksu['success_since'] = today


	if user_action == 'Fail_Confirm':
		ksu['streak'] = "0"
		ksu['success_since'] = None

	update_theory(theory, ksu_set)
	return




def update_ksu_in_mission(theory, post_details):
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	valid_sets = ['KAS1', 'KAS2', 'BOKA']	
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
		ksu['in_upcoming'] = True
		ksu['in_mission'] = False		

	update_theory(theory, ksu_set)	
	return



def update_ksu_status(theory, post_details):
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	valid_sets = ['KAS2', 'BigO', 'BOKA']	
	if set_name not in valid_sets:
		return

	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]	
	user_action = post_details['action_description']

	if user_action == 'Done_Confirm' or user_action == 'Done_Confirm_Continue':
		ksu['status'] = 'Done'
		ksu['is_visible'] = False
	
	elif user_action == 'Achieved_Confirm':
		ksu['status'] = 'Achieved'
		ksu['is_visible'] = False

	update_theory(theory, ksu_set)

	return




def update_MLog(theory, event):
	MLog = unpack_set(theory.MLog)

	date = event['date']
	event_type = event['type']
	score_events = ['EndValue','SmartEffort','Stupidity', 'Achievement']

	if event_type in score_events:
		event_score = calculate_event_score(event)
		log = MLog[date]
		for (units, score) in list(event_score.items()):
			log[units] = log[units] + score

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
	if set_name == 'KAS2':
		theory.KAS2 = pack_set(ksu_set)
	if set_name == 'KAS3':
		theory.KAS3 = pack_set(ksu_set)
	if set_name == 'KAS4':
		theory.KAS4 = pack_set(ksu_set)

	if set_name == 'BigO':
		theory.BigO = pack_set(ksu_set)
	if set_name == 'BOKA':
		theory.BOKA = pack_set(ksu_set)

	if set_name == 'ImPe':
		theory.ImPe = pack_set(ksu_set)
	return






#---Templates---

#General Attributes
i_BASE_KSU = {'id': None,
		      'parent_id': None,
		      'subtype':None,
		      'status':'Active', # ['Active', 'Done', 'Hold', 'Deleted']
	    	  'description': None,	    	  
	    	  'is_visible': True,
		      'is_private': False,
	    	  'local_tags': None, #la idea es que el atributo sea una lista con varios elementos, ahora en esta primera version solo hay espeacio para uno (80/20)
	    	  'global_tags': None, #la idea es que el atributo sea una lista con varios elementos, ahora en esta primera version solo hay espeacio para uno (80/20)
	    	  'comments': None}


i_KAS_KSU = {'value_type':None,
			 'importance':"3", # the higher the better.
	    	 'is_critical': False}


i_Proactive_KAS_KSU = {'time_cost': "1", # Reasonable Time Requirements in Minutes
					   'in_mission':False,
			 		   'any_any':False, # This particular action can be executed at anytime and in anyplace
			           'in_upcoming':True,
			           'next_event':None,
			           'best_time': None,}


i_Reactive_KAS_KSU = {'circumstance':None,
					  'exceptions':None,
					  'success_since':None,
			  		  'streak':"0",
			  		  'record':"0"}



#KAS1 Specifics	- Resource Generation Core Set - Acciones Recurrentes Proactivas con el objetivo de generar recursos	
i_KAS1_KSU = {'charging_time': "7",
			  'last_event': None,
			  'project':None,
			  'best_day': "None",
			  'TimeUse_target_min':None, #xx
			  'TimeUse_target_max':None} 



i_KAS2_KSU = {'value_type':None,
			  'project':None,
			  'importance':"3", # the higher the better. Used to calculate FRP (Future Rewards Points). All KSUs start with a relative importance of 3
	    	  'time_cost': "13", # Reasonable Time Requirements in Minutes
	    	  'next_event':today}




#KAS3 Specifics - Acciones Reactivas Recurrentes con el objetivo de ejecutar una accion
i_KAS3_KSU = {'value_type':None} 


#KAS3 Specifics - Acciones Reactivas Recurrentes
i_KAS4_KSU = {'value_type':None}
			  


i_BigO_KSU = {'value_type':None,
			  'awesomeness':None, #How much awesomeness do you believe that achieving this goal would add to your life. Fibbo Scale. Can actually be 0. Formely known as achievement points.
			  'is_milestone':False,
			  'target_date':today+90} # if no target date is provided is automatically calculated based on days required			  
			  


# Big Objective Key Actions Set Specifics
i_BOKA_KSU = {'in_upcoming':False, #To overwrite the proactiveness auto true
			  'importance':"3",
			  'priority':"5",
			  'next_event':today}



i_Wish_KSU = {'value_type': None,
			  'awesomeness':None, #How much awesomeness do you believe that achieving this goal would add to your life. Fibbo Scale. Can actually be 0. Formely known as achievement points.			  
			  'bucket_list':False,
			  'milestone_target_date':None} #This is seen as 'milestone Target Date' only if this dream is also consider a milestone.



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




#xx
# Possible indicators subtypes # Score, AcumulatedPerception, RealitySnapshot, TimeUse
i_ImIn_KSU = {'relevant':True, #users cannot create their own indicators, so here they choose if this one in particular they find relevantamolavida
			  'value_type':None, #Indicator of the precense/absence of a certain value_type
			  'measurement_units':None,

			  'measurement_best_time':None,
			  'measurement_frecuency':None,
			  'next_measurement':None,

			  'target_min':None,
			  'target_max':None,
			  'question':None,
			  'reverse':False}


i_ImIn_Event = {'type':'Measurement',
				'value':None}




i_BASE_Event = {'id':None,
				'ksu_id':None,
				'date':today,
				'type':None} # Created, Edited, Deleted, EndValue, SmartEffort or Stupidity


i_Created_Event = {'type':'Created'}

i_Edited_Event = {'type':'Edited',
				  'changes':None}

i_Deleted_Event = {'type':'Deleted',
				   'reason':None}


i_Score_Event = {'value':None, # Points Earned
				 'importance':None} 


i_EndValue_Event = {'type':'EndValue',
					'duration':None, # To calculate Amount of SmartEffort Points Earned
					'effort':False}


i_SmartEffort_Event = {'type':'SmartEffort',
					   'duration':None, # To calculate Amount of SmartEffort Points Earned
			    	   'joy':False,
			    	   'disconfort':False,
			    	   'streak':None}



i_Stupidity_Event = {'type':'Stupidity',
					 'streak':None}



i_Achievement_Event = {'type':'Achievement',
					   'awesomeness':None,
					   'target_date':None,
					   'comments':None,
					   'met_expectations':False}





template_recipies = {'KAS1_KSU':[i_BASE_KSU, i_KAS_KSU, i_Proactive_KAS_KSU, i_KAS1_KSU],
					 'KAS2_KSU':[i_BASE_KSU, i_KAS_KSU, i_Proactive_KAS_KSU, i_KAS2_KSU],
					 'KAS3_KSU':[i_BASE_KSU, i_KAS_KSU, i_Reactive_KAS_KSU, i_KAS3_KSU],
					 'KAS4_KSU':[i_BASE_KSU, i_KAS_KSU, i_Reactive_KAS_KSU, i_KAS4_KSU],

					 'BigO_KSU':[i_BASE_KSU, i_BigO_KSU],
					 'BOKA_KSU':[i_BASE_KSU, i_Proactive_KAS_KSU, i_BOKA_KSU],

					 'ImPe_KSU':[i_BASE_KSU, i_ImPe_KSU],
					 'ImIn_KSU':[i_BASE_KSU, i_ImIn_KSU],
					 
					 'Created_Event':[i_BASE_Event, i_Created_Event],
					 'Edited_Event':[i_BASE_Event, i_Edited_Event],
					 'Deleted_Event':[i_BASE_Event, i_Deleted_Event],

					 'EndValue_Event':[i_BASE_Event, i_Score_Event, i_EndValue_Event],
					 'SmartEffort_Event':[i_BASE_Event, i_Score_Event, i_SmartEffort_Event],
					 'Stupidity_Event':[i_BASE_Event, i_Score_Event, i_Stupidity_Event],
					 'Achievement_Event':[i_BASE_Event, i_Achievement_Event]}




def make_ksu_template(set_name):
	template = {}
	target_template = set_name + '_KSU'
	template_recipe = template_recipies[target_template]
	for ingredient in template_recipe:
		for (attribute,value) in ingredient.items():
			template[attribute] = value
	return template



def make_event_template(event_type):
	template = {}
	target_template = event_type + '_Event'
	template_recipe = template_recipies[target_template]
	for ingredient in template_recipe:
		for (attribute,value) in ingredient.items():
			template[attribute] = value
	return template





#--- Create new Sets --- 



def new_set_KSU(set_name):
	result = {}
	ksu = make_ksu_template(set_name)
	ksu['set_size'] = 0
	ksu['id'] = set_name +'_0'
	ksu['set_type'] = set_name
	ksu['is_visible'] = False
	
	attributes = list(ksu.keys())
	if 'next_event' in attributes:
		ksu['next_event'] = None

	result['set_details'] = ksu
	return pack_set(result)



def new_set_Hist():
	result = {}
	event = make_event_template('Created')
	event['id'] = 'Event_0'
	event['set_type'] = 'Event'
	event['set_size'] = 0
	result['set_details'] = event
	return pack_set(result)



def new_set_MLog(start_date=(735964), end_date=(735964+366)): #start_date = Jan 1, 2016 |  end_date = Dec 31, 2016  
	result = {}
	for date in range(start_date, end_date):
		entry = {'EndValue':0, 'SmartEffort':0, 'Stupidity':0, 'Achievement':0}
		entry['date'] = datetime.fromordinal(date).strftime('%d-%m-%Y')
		result[date] = entry
	return pack_set(result)




#--- Create new Set Items ---


def new_ksu(self, set_name):
	theory = self.theory
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = make_ksu_template(set_name)
	ksu_id = create_id(ksu_set)
	ksu['id'] = ksu_id
	return ksu


def new_event(Hist, event_type):
	event = make_event_template(event_type)
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
	event = new_event(Hist, 'Created')
	event['ksu_id'] = ksu_id
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event



def add_Edited_event(theory, ksu, changes):
	Hist = unpack_set(theory.Hist)
	ksu_id = ksu['id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'Edited')
	event['ksu_id'] = ksu_id
	event['changes'] = changes
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event



def add_Deleted_event(theory, ksu):
	Hist = unpack_set(theory.Hist)
	ksu_id = ksu['id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'Deleted')
	event['ksu_id'] = ksu_id
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event





def add_EndValue_event(theory, post_details): #Duration & Importance to be updated from the post detail given that it could change
	Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'EndValue')

	if 'effort' in post_details:
		event['effort'] = True

	event['ksu_id'] = ksu_id
	event['duration'] = post_details['duration']
	event['importance'] = post_details['importance']	
	
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event




def add_SmartEffort_event(theory, post_details): #Duration & Importance to be updated from the post detail given that it could change
	Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'SmartEffort') 
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]
	poractive_sets = ['KAS1', 'KAS2', 'BOKA']
	reactive_sets = ['KAS3', 'KAS4']
	
	event['ksu_id'] = ksu_id
	
	if set_name in poractive_sets:		
		event['duration'] = post_details['duration']
		event['importance'] = post_details['importance']
		if 'joy' in post_details:
			event['joy'] = True
		if 'disconfort' in post_details:
			event['disconfort'] = True

	if set_name in reactive_sets:
		event['importance'] = ksu['importance']
		event['streak'] = ksu['streak']
		
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)
	return event




def add_Achievement_event(theory, post_details):
	Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'Achievement') 
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]

	event['ksu_id'] = ksu_id
	event['awesomeness'] = ksu['awesomeness']
	event['target_date'] = ksu['target_date']
	event['comments'] = post_details['comments']

	if 'met_expectations' in post_details:
		event['met_expectations'] = True
	
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)


	return event




def add_Stupidity_event(theory, post_details):
	Hist = unpack_set(theory.Hist)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	event = new_event(Hist, 'Stupidity')
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = ksu_set[ksu_id]

	event['ksu_id'] = ksu_id
	event['importance'] = ksu['importance']
	event['streak'] = ksu['streak']
	
	update_set(Hist, event)
	update_MLog(theory, event)
	theory.Hist = pack_set(Hist)	
	return





def calculate_event_score(event):
	result = {'EndValue':0,'SmartEffort':0, 'Stupidity':0, 'Achievement':0}

	poractive_sets = ['KAS1', 'KAS2', 'BOKA']
	reactive_sets = ['KAS3', 'KAS4']
	set_name = get_type_from_id(event['ksu_id'])
	event_type = event['type']

	if event_type == 'EndValue':
		result['EndValue'] = event['value'] = int(event['duration']) * int(event['importance'])
		result['SmartEffort'] = 20 * event['effort']

	elif event_type == 'SmartEffort':

		if set_name in poractive_sets:		
			result['SmartEffort'] = int(event['duration'])*(int(event['importance']) + event['disconfort']) 
			result['EndValue'] = int(event['duration'])*event['joy']
			
		if set_name in reactive_sets: 
			if int(event['importance']) < int(event['streak']):
				result['SmartEffort'] = int(event['importance']) * 2
			else:
				result['SmartEffort'] = int(event['importance']) + int(event['streak'])

	elif event_type == 'Stupidity':

		if int(event['importance']) < int(event['streak']):
			result['Stupidity'] = int(event['importance']) * 2
		else:
			result['Stupidity'] = int(event['importance']) + int(event['streak'])

	elif event_type == 'Achievement':
		result['Achievement'] = int(event['awesomeness'])
	
	return result






def add_ksu_to_set(self, set_name):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_set = unpack_set(eval('theory.' + set_name))
	ksu = make_ksu_template(set_name)
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
	checkboxes = ['is_critical', 'is_private', 'in_upcoming', 'any_any', 'is_milestone']
	details = {'is_critical':False,
			   'is_private':False,
			   'in_upcoming':False,
			   'any_any':False,
			   'local_tags':None,
	    	   'global_tags':None,
	    	   'is_milestone':False,
	    	   'comments':None}

	for (attribute, value) in post_details.items():
		
		if attribute in checkboxes:
			details[attribute] = True
		
		elif attribute in date_attributes:
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
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	set_name = get_type_from_id(ksu_id)
	ksu_set = unpack_set(eval('theory.' + set_name))
	old_ksu = ksu_set[ksu_id]
	ksu = add_edited_ksu_to_set(self)
	changes = determine_edit_changes(ksu, old_ksu)
	add_Edited_event(theory, ksu, changes)
	trigger_additional_actions(self)
	theory.put()
	return


def determine_edit_changes(new_ksu, old_ksu):
	changes ={}
	attributes = list(new_ksu.keys())
	for attribute in attributes:
		if new_ksu[attribute] != old_ksu[attribute]:
			changes[attribute] = old_ksu[attribute]
	return changes





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
	update_ksu_status(theory, post_details)
	update_ksu_streak_and_record(theory, post_details)
	trigger_additional_actions(self)
	theory.put()
	return



def user_Action_Done_Achievement(self):
	theory = self.theory
	post_details = get_post_details(self)
	add_Achievement_event(theory, post_details) 
	update_ksu_status(theory, post_details) 
	trigger_additional_actions(self)
	theory.put()
	return



def user_Action_Fail_Stupidity(self):
	theory = self.theory
	post_details = get_post_details(self)	
	add_Stupidity_event(theory, post_details)
	update_ksu_streak_and_record(theory, post_details)
	trigger_additional_actions(self)
	theory.put()
	return


def user_Action_Done_EndValue(self):
	theory = self.theory
	post_details = get_post_details(self)
	update_ksu_next_event(theory, post_details)
	update_ksu_in_mission(theory, post_details)
	add_EndValue_event(theory, post_details)
	update_ksu_status(theory, post_details)
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
		
		if ksu_type == 'KAS1':
			triggered_Action_create_KAS1_next_event(self)

		elif ksu_type == 'BOKA':
			triggered_Action_BOKA_add_value_type(self)	
		
		elif ksu_type == 'ImPe':
				triggered_Action_create_ImPe_Contact(self)		

  	if action_type == 'Save':
  		if ksu_type == 'ImPe':
  			triggered_Action_update_ImPe_Contact(self)

		if ksu_type =='BigO':
			triggered_Action_BOKA_update_value_type(self)

	if action_type == 'Done_Confirm':
		
		if ksu_subtype == 'ImPe_Contact':
			triggered_Action_Done_ImPe_Contact(self)


	if action_type == 'Achieved_Confirm':

		if ksu_type == 'BigO':
			triggered_Action_delete_BOKA_remains(self)


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
		ksu['next_event'] = today
	update_set(KAS1, ksu)
	theory.KAS1 = pack_set(KAS1)
	return




def triggered_Action_create_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	ImPe = unpack_set(theory.ImPe)
	KAS1 = unpack_set(theory.KAS1)
	person = ImPe[ksu_id]
	ksu = make_ksu_template('KAS1')
	ksu_id = create_id(KAS1)
	ksu['id'] = ksu_id
	ksu['value_type'] = 'V500'
	ksu['description'] = 'Contact ' + person['description']
	ksu['charging_time'] = person['contact_frequency']
	if person['last_contact']:
		ksu['last_event'] = person['last_contact']
		ksu['next_event'] = int(person['last_contact']) + int(person['contact_frequency'])
	else:
		ksu['next_event'] = today
	person['next_contact'] = ksu['next_event']	
	ksu['time_cost'] = 3
	ksu['parent_id'] = person['id']
	ksu['subtype'] = 'ImPe_Contact'
	person['contact_ksu_id'] = ksu['id']
	update_set(KAS1, ksu)
	update_set(ImPe, person)
	theory.KAS1 = pack_set(KAS1)
	theory.ImPe = pack_set(ImPe)
	add_Created_event(theory, ksu)
	return ksu


def triggered_Action_BOKA_add_value_type(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	BigO = unpack_set(theory.BigO)
	BOKA = unpack_set(theory.BOKA)
	
	ksu = BOKA[ksu_id]
	objective = BigO[ksu['parent_id']]
	ksu['value_type'] = objective['value_type']

	update_set(BOKA, ksu)
	theory.BOKA = pack_set(BOKA)
	return


def triggered_Action_BOKA_update_value_type(self):
	theory = self.theory
	post_details = get_post_details(self)
	BigO_id = post_details['ksu_id']
	BigO = unpack_set(theory.BigO)
	BOKA = unpack_set(theory.BOKA)
	objective = BigO[BigO_id]

	for (ksu_id, ksu) in BOKA.items():
		if ksu['parent_id'] == BigO_id:
			ksu['value_type'] = objective['value_type']

	update_set(BOKA, ksu)
	theory.BOKA = pack_set(BOKA)
	return




def triggered_Action_update_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	ImPe = unpack_set(theory.ImPe)
	KAS1 = unpack_set(theory.KAS1)
	person = ImPe[ksu_id]
	ksu_id = person['contact_ksu_id']
	ksu = KAS1[ksu_id]
	old_ksu = make_ksu_copy(ksu)
	ksu['description'] = 'Contact ' + person['description']
	ksu['charging_time'] = person['contact_frequency']
	if person['last_contact']:
		ksu['last_event'] = person['last_contact']
		ksu['next_event'] = int(person['last_contact']) + int(person['contact_frequency'])
	else:
		ksu['next_event'] = today
	person['next_contact'] = ksu['next_event']	
	update_set(KAS1, ksu)
	update_set(ImPe, person)
	changes = determine_edit_changes(ksu, old_ksu)
	theory.KAS1 = pack_set(KAS1)
	theory.ImPe = pack_set(ImPe)
	add_Edited_event(theory, ksu, changes)
	return


def make_ksu_copy(ksu):
	result = {}
	for (key, value) in ksu.items():
		result[key] = value
	return result



def triggered_Action_delete_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	person_id = post_details['ksu_id']
	ImPe = unpack_set(theory.ImPe)
	KAS1 = unpack_set(theory.KAS1)
	person = ImPe[person_id]
	ksu_id = person['contact_ksu_id']
	ksu = KAS1[ksu_id]
	ksu['status'] = 'Deleted'
	ksu['is_visible'] = False
	update_set(KAS1, ksu)
	theory.KAS1 = pack_set(KAS1)
	add_Deleted_event(theory, ksu)
	return




def triggered_Action_Done_ImPe_Contact(self):
	theory = self.theory
	post_details = get_post_details(self)
	ksu_id = post_details['ksu_id']
	KAS1 = unpack_set(theory.KAS1)
	ksu = KAS1[ksu_id]
	person_id = ksu['parent_id']
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
	standard_sets = ['KAS2','KAS3', 'KAS4', 'BigO', 'BOKA'] 

	if set_name in standard_sets:
		developer_Action_Load_Set_CSV(theory, set_name, csv_path)

	if set_name == 'KAS1':
		developer_Action_Load_KAS1_CSV(theory, csv_path)

	if set_name == 'ImPe':
		developer_Action_Load_ImPe_CSV(theory, csv_path)

	if set_name == 'All':
		developer_Action_Load_KAS1_CSV(theory, create_csv_path('KAS1'))
		developer_Action_Load_Set_CSV(theory, 'KAS2', create_csv_path('KAS2'))
		developer_Action_Load_Set_CSV(theory, 'KAS3', create_csv_path('KAS3'))
		developer_Action_Load_Set_CSV(theory, 'KAS4', create_csv_path('KAS4'))

		developer_Action_Load_Set_CSV(theory, 'BigO', create_csv_path('BigO'))
		developer_Action_Load_Set_CSV(theory, 'BOKA', create_csv_path('BOKA'))

		developer_Action_Load_ImPe_CSV(theory, create_csv_path('ImPe'))
		
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
	ksu = make_ksu_template(set_name)
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
		ksu['next_event'] = today
	update_set(KAS1, ksu)
	theory.KAS1 = pack_set(KAS1)
	return




def csv_triggered_Action_create_ImPe_Contact(theory, person):
	ImPe = unpack_set(theory.ImPe)
	KAS1 = unpack_set(theory.KAS1)
	ksu = make_ksu_template('KAS1')
	ksu_id = create_id(KAS1)
	ksu['id'] = ksu_id
	ksu['value_type'] = 'V500'
	ksu['description'] = 'Contact ' + person['description']
	ksu['charging_time'] = person['contact_frequency']
	if person['last_contact']:
		ksu['last_event'] = person['last_contact']
		ksu['next_event'] = int(person['last_contact']) + int(person['contact_frequency'])
	else:
		ksu['next_event'] = today
	person['next_contact'] = ksu['next_event'] 	
	ksu['time_cost'] = 3
	ksu['parent_id'] = person['id']
	ksu['subtype'] = 'ImPe_Contact'
	person['contact_ksu_id'] = ksu['id']
	update_set(KAS1, ksu)
	update_set(ImPe, person)
	theory.KAS1 = pack_set(KAS1)
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
	
	validation_attributes = ['username', 'password', 'description', 'charging_time', 'duration', 'last_event', 'next_event', 'target_date', 'comments']
	date_attributes = ['last_event', 'next_event', 'target_date']

	if target_attribute not in validation_attributes:
		return None
	error_key = target_attribute + '_error' 
		
	if target_attribute in date_attributes:
		if valid_date(user_input):
			return None
		else:
			return d_RE[error_key]

	elif d_RE[target_attribute].match(user_input):
		return None
	
	else:
		return d_RE[error_key]



d_RE = {'username': re.compile(r"^[a-zA-Z0-9_-]{3,20}$"),
		'username_error': 'Invalid Username Syntax',
		
		'password': re.compile(r"^.{3,20}$"),
		'password_error': 'Invalid Password Syntax',
		
		'email': re.compile(r'^[\S]+@[\S]+\.[\S]+$'),
		'email_error': 'Invalid Email Syntax',

		'description': re.compile(r"^.{5,200}$"),
		'description_error': 'Descriotion max lenght is 200 characters and min 5.',

		'charging_time': re.compile(r"^[0-9]{1,3}$"),
		'charging_time_error': 'Charging Time should be an integer with maximum 3 digits',

		'duration': re.compile(r"^[0-9]{1,3}$"),
		'duration_error': 'Duration should be an integer with maximum 3 digits',

		'last_event_error':'Last event format must be DD-MM-YYYY',
		'next_event_error':'Next event format must be DD-MM-YYYY',
		'target_date_error':'Target date format must be DD-MM-YYYY',

		'comments': re.compile(r"^.{0,400}$"),
		'comments_error': 'Comments cannot excede 400 characters'}






#---Global Variables ------------------------------------------------------------------------------


date_attributes = ['last_event', 'next_event', 'last_contact', 'next_contact', 'target_date']

l_Fibonacci = ['1','2','3','5','8','13','21','34','55','89','144','233','377','610','987']


l_Small_Fibonacci = ['1','2','3','5','8','13','21']


d_Values = {'V000': '0. End Value',
			'V100': '1. Inner Peace & Consciousness',
			'V200': '2. Fun & Excitement', 
			'V300': '3. Meaning & Direction', 
			'V400': '4. Health & Vitality', 
			'V500': '5. Love & Friendship', 
			'V600': '6. Knowledge & Skills', 
			'V700': '7. Outer Order & Peace', 
			'V800': '8. Stuff',
		 	'V900': '9. Money & Power'}

l_Values = sorted(d_Values.items())



d_Days = {'None':'None',
		  '1':'1. Sunday',
		  '2':'2. Monday',
		  '3':'3. Tuesday',
		  '4':'4. Wednesday',
		  '5':'5. Thursday',
		  '6':'6. Friday',
		  '7':'7. Saturday'}


l_default_grouping = [(True,'Showing All')]


l_Days = sorted(d_Days.items())


constants = {'l_Fibonacci':l_Fibonacci,
			 'l_Values':l_Values,
			 'l_Days':l_Days,}





d_Viewer ={'KAS1':{'set_title':'Proactive Value Creation Actions Core Set  (KAS1)',
				    'set_name':'KAS1',
				    'attributes':['description','charging_time','importance','pretty_next_event'],
				    'fields':{'description':'Description','charging_time':'C. Time','importance':'Exp. Imp.', 'pretty_next_event':'Next Event'},
				    'columns':{'description':5,'charging_time':1,'importance':1,'pretty_next_event':2},
				    'show_Button_Done':True,
				    'show_Button_Add_To_Mission':True,
				    'grouping_attribute':'value_type',
				    'grouping_list':l_Values},


			'KAS2':{'set_title':'Proactive Value Creation Actions Expantion Set  (KAS2)',
				    'set_name':'KAS2',
				    'attributes':['description','pretty_next_event','project'],
				    'fields':{'description':'Action description', 'pretty_next_event':'Event Date', 'project':'Project (if any)'},
				    'columns':{'description':5,'pretty_next_event':2,'project':2},
				    'show_Button_Done':True,
				    'show_Button_Add_To_Mission':True,
				    'grouping_attribute':'value_type',
				    'grouping_list':l_Values},


			'KAS3':{'set_title':'Reactive Value Creation Actions Set (KAS3)',
				    'set_name':'KAS3',
				    'attributes':['circumstance','description','streak','record'],
				    'fields':{'circumstance': 'Circumstance','description':'Target Reaction','streak':'Streak','record':'Record'},
				    'columns':{'circumstance':3,'description':4,'streak':1,'record':1},
				    'show_Button_Done':True,
				    'show_Button_Fail':True,
				    'grouping_attribute':'value_type',
				    'grouping_list':l_Values},


			'KAS4':{'set_title':'Value Destruction Actions Set -- To be avoided  (KAS4)',
				    'set_name':'KAS4',
				    'attributes':['description','circumstance','reaction','streak','record'],
				    'fields':{'description':'Action to Avoid','circumstance':'Dangerous Circumstances & Potential Reactions', 'streak':'Streak','record':'Record'},
				    'columns':{'description':3,'circumstance':4,'streak':1,'record':1},				    
				    'show_Button_Avoided':True,
				    'show_Button_Fail':True,
				    'grouping_attribute':'value_type',
				    'grouping_list':l_Values},


			'BigO':{'set_title':'Big Objectives Set  (BigO)', #ToBeDeleted once BigO have its custom SetViewer esto es nada mas pa que funcione por ahora
				    'set_name':'BigO',
				    'attributes':['id', 'description','pretty_target_date'],
				    'fields':{'description':'Objective description', 'pretty_target_date':'Target Date', 'id':'ID'},
				    'columns':{'description':5, 'pretty_target_date':2, 'id':1},
				    'show_Button_Achieved':True,
				    'show_Button_Add_Child_KSU':True,				    
				    'grouping_attribute':'local_tags',
				    'grouping_list':None},


			'BOKA':{'set_title':'Big Objectives Key Actions Set  (BOKA)', #ToBeDeleted once BigO have its custom SetViewer esto es nada mas pa que funcione por ahora
				    'set_name':'BOKA',
				    'attributes':['parent_id', 'description', 'priority', 'pretty_target_date'],
				    'fields':{'parent_id':'BigO id','priority':'Priority','description':'Action description', 'pretty_target_date':'Target Date'},
				    'columns':{'parent_id':1, 'description':5, 'priority':1, 'pretty_target_date':2},
				    'show_Button_Done':True,
				    'show_Button_Add_To_Mission':True,			    
				    'grouping_attribute':'local_tags',
				    'grouping_list':None},

		   
		   'ImPe': {'set_title':'My Important People',
		   			'set_name':'ImPe',
					'attributes':['description', 'contact_frequency', 'pretty_last_contact', 'pretty_next_contact', 'comments'],
				    'fields':{'description':'Name', 'contact_frequency':'C. Freq.', 'pretty_last_contact':'Last Contact', 'pretty_next_contact':'Next Contact', 'comments':'Comments'},
				    'columns':{'description':3, 'contact_frequency':1, 'pretty_last_contact':2, 'pretty_next_contact':2, 'comments':3},
				    'show_Button_Done':False,
				    'show_Button_Add_To_Mission':False,
				    'grouping_attribute':'local_tags',
				    'grouping_list':None},


			'ImPe': {'set_title':'Events History',
		   			'set_name':'Hist',
					'attributes':['id', 'ksu_id', 'type'],
				    'fields':{'id':'Event ID', 'ksu_id':'KSU ID', 'type':'Event Type'},
				    'columns':{'id':1, 'ksu_id':1, 'type':2},
				    'grouping_attribute':'date',
				    'grouping_list':None}}


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
                             

                             ('/SetViewer/' + PAGE_RE, SetViewer),
                             ('/BigOViewer', BigOViewer),

                             ('/TodaysMission', TodaysMission),
                             ('/Upcoming', Upcoming),
                             ('/effort-report',EffortReport),
							 
							 ('/NewKSU/' + PAGE_RE, NewKSU),
							 ('/EditKSU', EditKSU),
							 
							 ('/Done', Done),
							 ('/Failure', Failure),
							 
							 ('/email',Email),
							 ('/LoadCSV/' + PAGE_RE, LoadCSV),
							 ('/csv-backup',CSVBackup),
							 ('/PythonBackup/' + PAGE_RE, PythonBackup)
							 ], debug=True)
