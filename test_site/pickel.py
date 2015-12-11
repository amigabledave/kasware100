import pickle

test_list = [1,2,"Dave",{'amor':'felicidad'}]


# pickle_test = pickle.dumps(test_list)
# print pickle_test
# print pickle.loads(pickle_test)


lista_a_texto = str(test_list)

print lista_a_texto
print eval(lista_a_texto)