from __future__ import unicode_literals
from frappe import _

def get_data():
    return {
        'fieldname': 'material_consumption',
        'transactions': [
            {
                'label': _('Stock Entry'),
                'items': ['Stock Entry']
            }
        ]
    }