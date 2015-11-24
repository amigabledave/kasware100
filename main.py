#KASware v1.0.0 | Copyright 2015 AmigableDave & Co.

import re, os, webapp2, jinja2
from google.appengine.ext import db
from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'html_templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)


### Handlers ###

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_html(self, template, **kw):
		t = jinja_env.get_template(template)
		return t.render(**kw)

	def print_html(self, template, **kw):
		self.write(self.render_html(template, **kw))


class Home(Handler):
    def get(self):
        self.print_html('home.html')


class NewKSU(Handler):
	def get(self):
		self.print_html('ksu-edit-form.html', elements = list_elements_cat)

###



### DataStore Entities ###

class User_Theory(db.Model):
	user_name = db.StringProperty(required=True)
	kba_set = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)


###


### Global Constants ###
list_elements_cat = ['1. Fun & Excitement', '2. Meaning & Direction', '3. Health & Vitality', '4. Love & Friendship', '5. Knowledge & Skills', '6. Outer Peace', '7. Money & Resources', '8. Inner Peace']
###




app = webapp2.WSGIApplication([
							 ('/', Home),
							 ('/newksu', NewKSU)
							 ], debug=True)
