dictionary = {'uno':1,'dos':2,'letra a':'a'}


d_Elements = {'E100': '1. Inner Peace',
			 'E200': '2. Fun & Excitement', 
			 'E300': '3. Meaning & Direction', 
			 'E400': '4. Health & Vitality', 
			 'E500': '5. Love & Friendship', 
			 'E600': '6. Knowledge & Skills', 
			 'E700': '7. Outer Peace', 
			 'E800': '8. Monetary Resources',
		 	 'E900': '9. Non-Monetary Resources'}



# prueba = list(dictionary.values())
# print prueba

# print 'chango' in dictionary


# for (key,value) in dictionary.items(): # dict.items() returns a list of 2-tuples ([(key, value), (key, value), ...])
# 	print str(key) + " corresponde a " + str(value)


# for (key,value) in dictionary.iteritems(): 
# 	print str(key) + " corresponde a " + str(value)


def reverse_dict(dictionary):
	result = {}
	for (key, value) in dictionary.items():
		result[value] = key
	return result

print list(d_Elements.values())
print reverse_dict(d_Elements)