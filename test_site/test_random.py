import random


i_post_details = {'ksu_id':None,
				  'duration':'0',
				  'repetitions':'1',
				  'importance':'3',
				  'effort':None, # whe true is 'on'
				  'joy':None,
				  'disconfort':None,
				  'met_expectations':None,
				  'comments':None}



random_post_details = {'ksu_id':None,
					  'duration':random.randrange(5, 120),
					  'repetitions':random.randrange(1, 5),
					  'importance':random.randrange(1, 13),
					  'effort':random.choice([None, 'on']), # whe true is 'on'
					  'joy':random.choice([None, 'on']),
					  'disconfort':random.choice([None, 'on']),
					  'met_expectations':random.choice([None, 'on']),
					  'comments':random.choice([None, 'Some random comments'])}
# print random_post_details




