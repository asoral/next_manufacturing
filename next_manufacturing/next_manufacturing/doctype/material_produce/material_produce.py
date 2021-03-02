# -*- coding: utf-8 -*-
# Copyright (c) 2021, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json

class MaterialProduce(Document):
	def set_produce_material(self):
		if self.material_produce_details:
			total_qty = 0
			line_id = None
			for res in self.material_produce_details:
				total_qty += res.qty_produced
				line_id = res.line_ref

			l_doc = frappe.get_doc("Material Produce Item", line_id)
			if l_doc.qty_produced:
				if total_qty > l_doc.qty_produced:
					frappe.throw(_("Can not allow total produced qty greater then {0}").format(l_doc.qty_produced))
			lst = []
			for res in self.material_produce_details:
				if res.qty_produced:
					lst.append({
						"item_code": res.item_code,
						"item_name": res.item_name,
						"t_warehouse": res.t_warehouse,
						"qty_produced": res.qty_produced,
						"has_batch_no": res.has_batch_no,
						"batch": res.batch,
						"rate": res.rate,
						"weight": res.weight,
						"line_ref": res.line_ref
					})
			if line_id:
				l_doc = frappe.get_doc("Material Produce Item", line_id)
				l_doc.data = json.dumps(lst)
				l_doc.qty_issued = total_qty
				l_doc.status = "Set"
				l_doc.save(ignore_permissions=True)
		return True

@frappe.whitelist()
def add_details_line(line_id,item_code, warehouse,qty_produced=0, data=None):
	if not data:
		item = frappe.get_doc("Item", item_code)
		lst=[]
		lst.append({
			"item_code": item.name,
			"item_name": item.item_name,
			"t_warehouse": warehouse,
			"qty_produced": qty_produced,
			"has_batch_no": item.has_batch_no,
			"weight": item.weight_per_unit,
			"line_ref":line_id
		})
		return lst
	else:
		return json.loads(data)