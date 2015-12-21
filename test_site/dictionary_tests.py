dictionary = {'uno':1,'dos':2,'letra a':'a'}


# prueba = list(dictionary.values())
# print prueba

# print 'chango' in dictionary


for (key,value) in dictionary.items(): # dict.items() returns a list of 2-tuples ([(key, value), (key, value), ...])
	print str(key) + " corresponde a " + str(value)


# for (key,value) in dictionary.iteritems(): 
# 	print str(key) + " corresponde a " + str(value)