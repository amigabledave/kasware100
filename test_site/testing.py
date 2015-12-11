

def create_effort_report(theory, date):
	result = []
	kas1 = eval(theory.kas1, {})
	for ksu in kas1:
		history = kas['history']
		for event in history:
			if event['event_date'] == date and event['event_type']=='Effort':
				report_item = {'effort_description':None,'effort_points':0}
				report_item['effort_description'] = ksu['description']
				report_item['effort_points'] = event['event_value']
				result.append(report_item)
	return result



