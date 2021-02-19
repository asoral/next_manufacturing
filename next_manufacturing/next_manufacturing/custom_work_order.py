from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from frappe.utils import flt, nowdate

def after_insert(self,method):
    sg =0.0
    cnt =0
    bmw = 0.0

    for itm in self.required_items:
        if itm.specific_gravity:
            sg += itm.specific_gravity
            cnt += 1
            bmw += itm.required_qty * itm.weight_per_unit
    if sg > 0 and cnt > 0:
        self.specific_gravity = sg/cnt
        self.bom_weight = bmw

    rm = 0.0
    for itm in self.required_items:
        if itm.type == "RM":
            rm += itm.required_qty * itm.weight_per_unit
    self.rm_weight = rm

    self.fg_weight = self.qty * self.weight_per_unit
    if rm > 0:
        self.yeild = ((self.fg_weight / self.rm_weight) * 100)
    # self.save()

@frappe.whitelist()
def after_save(doc_name):
    doc = frappe.get_doc("Work Order",doc_name)
    sg =0.0
    cnt =0
    bmw = 0.0

    for itm in doc.required_items:
        if itm.specific_gravity:
            sg += itm.specific_gravity
            cnt += 1
            bmw += itm.required_qty * itm.weight_per_unit

    if sg > 0 and cnt > 0:
        doc.specific_gravity = sg/cnt
        doc.bom_weight = bmw
    # else:
    #     frappe.throw("Specific Gravity is Zero or There is Zero Item in Table")

    rm = 0.0
    for itm in doc.required_items:
        if itm.type == "RM":
            rm += itm.required_qty * itm.weight_per_unit

    doc.rm_weight = rm

    doc.fg_weight = doc.qty * doc.weight_per_unit

    if rm > 0:
        doc.yeild = ((doc.fg_weight / doc.rm_weight) * 100)
    # else:
    #     frappe.throw("Raw Material Weight is Zero")
    doc.save()


@frappe.whitelist()
def add_additional_fabric(doc_name, item_code, required_qty):
    print("---------------doc_name",doc_name, item_code, required_qty)
    wo = frappe.get_doc("Work Order", doc_name)
    wo.append("required_items", {
        "item_code":item_code,
        "source_warehouse": wo.source_warehouse,
        "required_qty":required_qty
    })
    wo.flags.ignore_validate_update_after_submit = True
    wo.set_available_qty()
    # wo.validate()
    wo.save(ignore_permissions=True)

    return True