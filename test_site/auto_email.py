Espacio = """

"""

nombres = ['Dave', 'Jimmy', 'Dani', 'Elena']


def mete_espacio(l):
	result = ""
	for e in l:
		result += ""e + Espacio
	return result

nombres_y_espacio = mete_espacio(nombres)

print nombres_y_espacio