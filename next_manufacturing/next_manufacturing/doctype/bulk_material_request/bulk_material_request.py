# -*- coding: utf-8 -*-
# Copyright (c) 2021, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import collections, functools, operator
from collections import defaultdict
from frappe.utils import nowdate
class BulkMaterialrequest(Document):
	def before_save(self):
		if (len(self.items) >0):
			mr = frappe.new_doc("Material Request")
			mr.set_warehouse = self.source_warehouse
			mr.required_by = nowdate()
			for i in self.items:
				q = """select conversion_factor from `tabUOM Conversion Detail` where parent='{0}' and uom='{1}';""".format(i.get('item_code'),i.get('uom'))
				con_factor = frappe.db.sql(q, as_dict = 1)[0].get('conversion_factor')
				mr.append('items', {
					'item_code': i.get('item_code'),
					'qty': i.get('qty_to_transfer'),
					# 'uom': i.get('uom'),
					# 'uom_conversion_factor': con_factor,
				})
			mr.insert()
			mr.submit()
	def get_item_list(self):
		all_work_order = frappe.db.get_all("Work Order", {"rm_store_warehouse": self.rm_store_warehouse, "source_warehouse":self.source_warehouse, "status":['!=','Complete']},['name'])
		item_list = []
		for wo in all_work_order:
			query = """select item_code,required_qty from `tabWork Order Item` where parent='{0}';""".format(wo.get('name'))
			#query = """select item_code,required_qty from `tabWork Order Item` where parent='{0}';""".format(wo.get('name'))
			all_items = frappe.db.sql(query, as_dict = True)
			for item in all_items:
				item_list.append(item)
		data_list = []
		for i in item_list:
			qty = int(i.get('required_qty'))
			d = {
				'item_code': i.get('item_code'),
				#'item_name': i.get('item_name'),
				'required_qty': qty
			}
			data_list.append(d)

		dic = {}
		for item in data_list:
			n, q = item.values()
			dic[n] = dic.get(n,0) + q
		#print(dic)

		shorted_data = [{'item_code':n, 'required_qty':q} for n,q in dic.items()]
		data = []
		for i in shorted_data:
			item_detail = frappe.db.get_value("Item", {"item_code":i.get("item_code")},['item_group','item_name','stock_uom'], as_dict = 1)
			avl_stock = frappe.db.get_value("Bin", {"item_code":i.get("item_code"),"warehouse":self.source_warehouse},['actual_qty','projected_qty'], as_dict = 1)
			qty_to_transfer = i.get('required_qty') - avl_stock.get('projected_qty')
			
			if qty_to_transfer > 0:
				data.append(
					{
					'item_code': i.get("item_code"),
					'item_name': item_detail.get('item_name'),
					'item_group': item_detail.get('item_group'),
					'projected_qty_at_source_warehouse': avl_stock.get('projected_qty'),
					'actual_qty_at_source_warehouse' : avl_stock.get('actual_qty'),
					'required_qty': i.get('required_qty'),
					'uom': item_detail.get('stock_uom'),
					'qty_to_transfer': qty_to_transfer
				}
				)

				# self.append("items", {
				# 	'item_code': i.get("item_code"),
				# 	'item_name': item_detail.get('item_name'),
				# 	'item_group': item_detail.get('item_group'),
				# 	'projected_qty_at_source_warehouse': avl_stock.get('projected_qty'),
				# 	'actual_qty_at_source_warehouse' : avl_stock.get('actual_qty'),
				# 	'required_qty': i.get('required_qty'),
				# 	'uom': item_detail.get('stock_uom'),
				# 	'qty_to_transfer': qty_to_transfer
				# })
		return data

