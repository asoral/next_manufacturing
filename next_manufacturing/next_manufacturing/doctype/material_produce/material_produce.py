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
                l_doc.qty_produced = total_qty
                l_doc.status = "Set"
                l_doc.save(ignore_permissions=True)
        return True

    def make_stock_entry(self):
        return self.make_se()

    def make_se(self):
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.work_order = self.work_order
        stock_entry.material_produce = self.name
        stock_entry.company = self.company
        stock_entry.stock_entry_type = "Manufacture"
        total_transfer_qty = 0

        wo = frappe.get_doc("Work Order",self.work_order)
        for res in wo.required_items:
            if res.transferred_qty:
                expense_account, cost_center = frappe.db.get_values("Company", self.company, ["default_expense_account", "cost_center"])[0]
                item_expense_account, item_cost_center = frappe.db.get_value("Item Default",
                                    {'parent': res.item_code,'company': self.company},["expense_account","buying_cost_center"])
                if not cost_center and not item_cost_center:
                    frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))

                itm_doc = frappe.get_doc("Item",res.item_code)
                se_item = stock_entry.append("items")
                se_item.item_code = res.item_code
                se_item.qty = res.transferred_qty
                se_item.s_warehouse = res.source_warehouse
                se_item.item_name = itm_doc.item_name
                se_item.description = itm_doc.description
                se_item.uom = itm_doc.stock_uom
                se_item.stock_uom = itm_doc.stock_uom
                se_item.expense_account = item_expense_account or expense_account
                se_item.cost_center = item_cost_center or cost_center
                # in stock uom
                se_item.conversion_factor = 1.00
        stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)
        for res in self.material_produce_item:
            if res.data:
                for line in json.loads(res.data):
                    expense_account, cost_center = frappe.db.get_values("Company", self.company, ["default_expense_account", "cost_center"])[0]
                    item_expense_account, item_cost_center = frappe.db.get_value("Item Default",
                                            {'parent': line.get('item_code'),'company': self.company},["expense_account","buying_cost_center"])
                    if not cost_center and not item_cost_center:
                        frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))

                    itm_doc = frappe.get_doc("Item", line.get('item_code'))
                    se_item = stock_entry.append("items")
                    se_item.item_code = line.get('item_code')
                    se_item.qty = line.get('qty_produced')
                    se_item.t_warehouse = line.get('t_warehouse')
                    se_item.item_name = itm_doc.item_name
                    se_item.description = itm_doc.description
                    se_item.uom = res.uom
                    se_item.stock_uom = res.uom
                    se_item.batch_no = line.get('batch')
                    se_item.expense_account = item_expense_account or expense_account
                    se_item.cost_center = item_cost_center or cost_center
                    se_item.is_finished_item = 1 if res.type == 'FG' else 0
                    se_item.is_scrap_item = 1 if res.type == 'Scrap' else 0
                    # in stock uom
                    if res.type == "FG":
                        total_transfer_qty += line.get('qty_produced')
                    se_item.conversion_factor = 1.00
        stock_entry.from_bom = 1
        stock_entry.fg_completed_qty = total_transfer_qty
        stock_entry.set_actual_qty()
        stock_entry.set_missing_values()
        # stock_entry.insert(ignore_permissions=True)
        # stock_entry.validate()
        return stock_entry.as_dict()


@frappe.whitelist()
def add_details_line(line_id,item_code, warehouse,qty_produced=None,batch_size=None, data=None):
    if qty_produced:
        qty_produced = float(qty_produced)
    else:
        qty_produced = 0
    if batch_size:
        batch_size = float(batch_size)
    else:
        batch_size = 0
    if not data:
        item = frappe.get_doc("Item", item_code)
        lst = []
        if item.has_batch_no and batch_size:
            remaining_size = qty_produced
            while True:
                if (remaining_size >= batch_size):
                    lst.append({
                        "item_code": item.name,
                        "item_name": item.item_name,
                        "t_warehouse": warehouse,
                        "qty_produced": batch_size,
                        "has_batch_no": item.has_batch_no,
                        "weight": item.weight_per_unit,
                        "line_ref": line_id
                    })
                else:
                    lst.append({
                        "item_code": item.name,
                        "item_name": item.item_name,
                        "t_warehouse": warehouse,
                        "qty_produced": remaining_size,
                        "has_batch_no": item.has_batch_no,
                        "weight": item.weight_per_unit,
                        "line_ref": line_id
                    })
                    break
                remaining_size -= batch_size
                if(remaining_size < 1):
                    break
        else:
            lst.append({
                "item_code": item.name,
                "item_name": item.item_name,
                "t_warehouse": warehouse,
                "qty_produced": qty_produced,
                "has_batch_no": item.has_batch_no,
                "weight": item.weight_per_unit,
                "line_ref": line_id
            })
        return lst
    else:
        return json.loads(data)