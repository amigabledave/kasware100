
# ksu_set = {'KSU1':{'reward':100}, 'KSU2':{'punishment':1}, 'KSU3':{'dog':True}}
# attributes_to_add = {'reward':'1', 'punishment':'34'}
# attributes_to_delete = {'dog'}
# attribute_key = 'punishment'
# attribute_value = '34'

def add_ksu_attribute_to_set(ksu_set, attribute_key, attribute_value):
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		if attribute_key not in ksu:						
			ksu[attribute_key] = attribute_value
	return ksu_set
# add_ksu_attribute_to_set(ksu_set, attribute_key, attribute_value)
# print ksu_set


def delete_ksu_attribute_in_set(ksu_set, attribute_key):
	for ksu in ksu_set:
		ksu = ksu_set[ksu]
		if attribute_key in ksu:			
			del ksu[attribute_key]
	return ksu_set

# delete_ksu_attribute_in_set(ksu_set, attribute_key)
# print ksu_set


def structure_update(ksu_set, attributes_to_add, attributes_to_delete):
	for (attribute_key, attribute_value) in list(attributes_to_add.items()):
		add_ksu_attribute_to_set(ksu_set, attribute_key, attribute_value)

	for attribute_key in attributes_to_delete:
		delete_ksu_attribute_in_set(ksu_set, attribute_key)

	return ksu_set

# attributes_to_add = {'reward':'1', 'punishment':'34'}
# attributes_to_delete = {'dog'}
# print structure_update(ksu_set, attributes_to_add, attributes_to_delete)

ksu_set = {}
attributes_to_add = {}
attributes_to_delete = {}

print structure_update(ksu_set, attributes_to_add, attributes_to_delete)


