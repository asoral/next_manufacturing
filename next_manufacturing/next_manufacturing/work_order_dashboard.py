from __future__ import unicode_literals
from frappe import _

def get_data(data):
	return {
		'fieldname': 'work_order',
		'transactions': [
			{
				'label': _('Transactions'),
				'items': ['Stock Entry', 'Job Card', 'Pick List','Material Request','Material Consumption','Material Produce','Additional Items']
			}
		],
		'Material': [
			{
				'label': _('Materials'),
				'items': ['Material Request', 'Material Consumption','Material Produce']
			}
		]
	}
