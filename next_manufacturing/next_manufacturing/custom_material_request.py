

from __future__ import unicode_literals
import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def create_pick_list(source_name, target_doc=None):
    doc = get_mapped_doc('Material Request', source_name, {
        'Material Request': {
            'doctype': 'Pick List',
            'field_map': {
                'material_request_type': 'purpose',
                'work_order': 'work_order'
            },
            'validation': {
                'docstatus': ['=', 1]
            }
        },
        'Material Request Item': {
            'doctype': 'Pick List Item',
            'field_map': {
                'name': 'material_request_item',
                'qty': 'stock_qty'
            },
        },
    }, target_doc)
    doc.set_item_locations()
    return doc