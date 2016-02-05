import pickle

def pack_set(ksu_set):
	return pickle.dumps(ksu_set)

def unpack_set(ksu_pickled_set):
	return pickle.loads(ksu_pickled_set)

