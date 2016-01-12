dictionary = {'uno':1,'dos':2,'letra a':'a'}


d_Elements = {'E100': '1. Inner Peace & Consciousness',
			  'E200': '2. Fun & Excitement', 
			  'E300': '3. Meaning & Direction', 
			  'E400': '4. Health & Vitality', 
			  'E500': '5. Love & Friendship', 
			  'E600': '6. Knowledge & Skills', 
			  'E700': '7. Outer Peace', 
			  'E800': '8. Monetary Resources',
		 	  'E900': '9. Non-Monetary Resources'}



# def reverse_dict(dictionary):
# 	result = {}
# 	for (key, value) in dictionary.items():
# 		result[value] = key
# 	return result
# print reverse_dict(d_Elements)



# prueba = list(dictionary.values())
# print prueba

# print 'chango' in dictionary


# for (key,value) in dictionary.items(): # dict.items() returns a list of 2-tuples ([(key, value), (key, value), ...])
# 	print str(key) + " corresponde a " + str(value)


# for (key,value) in dictionary.iteritems(): 
# 	print str(key) + " corresponde a " + str(value)

# print sorted(d_Elements.items())[3][1]



# print d_Elements

# del d_Elements['E100']
# del d_Elements['E200']
# del d_Elements['E300']
# del d_Elements['E400']
# del d_Elements['E500']
# del d_Elements['E600']

# print d_Elements

#

i_BASE_KSU = {'id': None,
		      'parent_id': None,
	    	  'element': None,
	    	  'description': None,
	    	  'comments': None,
	    	  'local_tags': None,
	    	  'global_tags': None}


#KAS Specifics
i_KAS_KSU = { 'status':'Active', # ['Active', 'Hold', 'Deleted']
	    	  'relative_imp':"3", # the higher the better. Used to calculate FRP (Future Rewards Points). All KSUs start with a relative importance of 3
	    	  'time_cost': "13", # Reasonable Time Requirements in Minutes
	    	  'in_mission': False,
	    	  'is_critical': False,
	    	  'is_visible': True,
	    	  'is_private': False, 
	    	  'subtype':None,
	    	  'target_person':None}


#KAS1 Specifics			
i_KAS1_KSU = {'frequency': "7",
			  'best_day': "None",
			  'best_time': None,
			  'last_event': None,
			  'next_event': None}


#ImPE Specifics
i_ImPe_KSU = {'contact_frequency':None, # Should be replaced with frequency
			  'last_contact':None, # Should be replaced with last event
			  'next_contact':None, # Should be replaced with next event
			  'fun_facts':None,
			  'email':None,
			  'phone':None,
			  'facebook':None,
			  'birthday':None,
			  'important_since':None,
			  'related_ksus':[]}


template_recipies = {'KAS1':[i_BASE_KSU, i_KAS_KSU, i_KAS1_KSU],
					 'ImPe':[i_BASE_KSU, i_ImPe_KSU]}



def make_ksu_template(set_name):
	template = {}
	template_recipe = template_recipies[set_name]
	for ingredient in template_recipies:
		print ingredient
		# for (attribute,value) in ingredient.items():
		# 	template[attribute] = value
	return template


# print make_ksu_template('KAS1')



# ---- Sorting ---

student_tuples = [
        ('john', 'A', 15),
        ('jane', 'B', 12),
        ('dave', 'B', 10)]

from operator import itemgetter
print sorted(student_tuples, key=itemgetter(2), reverse=True)






