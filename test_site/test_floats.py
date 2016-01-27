

# indicator_history = ['Yes','No', 'Yes', 'Yes', 'Yes','No', 'Yes', 'Yes', 'Yes', 'Yes', ]
# value = (sum(1.0 if x == 'Yes' else 0 for x in indicator_history))/len(indicator_history)

indicator_history = ['1.5', '8.9', '11.5']
value = (sum( float(x) for x in indicator_history))/len(indicator_history)


print value


