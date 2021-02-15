from __future__ import unicode_literals
import frappe

def after_insert(self,method):
    sg = 0.0
    cnt = 0
    bmw = 0.0

    for itm in self.required_items:
        if itm.specific_gravity:
            sg += itm.specific_gravity
            cnt += 1
            bmw += itm.required_qty * itm.weight_per_unit
    if cnt:
        self.specific_gravity = sg/cnt
    else:
        self.specific_gravity = 0
    self.bom_weight = bmw

    rm = 0.0
    for itm in self.required_items:
        if itm.type == "RM":
            rm += itm.required_qty * itm.weight_per_unit
    self.rm_weight = rm

    self.fg_weight = self.qty * self.weight_per_unit
    if self.rm_weight:
        self.yeild = ((self.fg_weight / self.rm_weight) * 100)
    else:
        self.yeild = 0

    self.save()

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
    if cnt:
        doc.specific_gravity = sg/cnt
    else:
        doc.specific_gravity = 0
    doc.bom_weight = bmw

    rm = 0.0
    for itm in doc.required_items:
        if itm.type == "RM":
            rm += itm.required_qty * itm.weight_per_unit

    doc.rm_weight = rm

    doc.fg_weight = doc.qty * doc.weight_per_unit
    if doc.rm_weight:
        doc.yeild = ((doc.fg_weight / doc.rm_weight) * 100)
    else:
        doc.yeild = 0
    doc.save()