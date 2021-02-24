from __future__ import unicode_literals
import frappe
from frappe import _


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
    frappe.clear_cache()
    wo = frappe.get_doc("Work Order", doc_name)
    wo_line = frappe.get_list("Work Order Item", filters={"item_code": item_code})
    if wo_line:
        woi_doc = frappe.get_doc("Work Order Item",wo_line[0].name)
        if woi_doc.required_qty:
            woi_doc.required_qty += float(required_qty)
        else:
            woi_doc.required_qty = required_qty
        wo.flags.ignore_validate_update_after_submit = True
        wo.set_available_qty()
        wo.save(ignore_permissions=True)
    else:
        wo.append("required_items", {
            "item_code":item_code,
            "source_warehouse": wo.source_warehouse,
            "required_qty":required_qty,
            "additional_material": 1,
            "include_item_in_manufacturing": 1
        })
        wo.flags.ignore_validate_update_after_submit = True
        wo.set_available_qty()
        wo.save(ignore_permissions=True)

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.work_order = wo.name
    stock_entry.stock_entry_type = "Material Transfer for Manufacture"
    expense_account, cost_center = frappe.db.get_values("Company", wo.company, ["default_expense_account", "cost_center"])[0]
    item_name, stock_uom, description = frappe.db.get_values("Item", item_code, ["item_name", "stock_uom", "description"])[0]

    item_expense_account, item_cost_center = frappe.db.get_value("Item Default", {'parent': item_code, 'company': wo.company}, ["expense_account", "buying_cost_center"])

    if not cost_center and not item_cost_center:
        frappe.throw(_("Please update default Cost Center for company {0}").format(wo.company))

    se_item = stock_entry.append("items")
    se_item.item_code = item_code
    se_item.qty = required_qty
    se_item.s_warehouse = wo.source_warehouse
    se_item.t_warehouse = wo.wip_warehouse
    se_item.item_name = item_name
    se_item.description = description
    se_item.uom = stock_uom
    se_item.stock_uom = stock_uom
    se_item.expense_account = item_expense_account or expense_account
    se_item.cost_center = item_cost_center or cost_center

    # in stock uom
    se_item.conversion_factor = 1.00
    stock_entry.set_actual_qty()
    stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)

    return stock_entry.as_dict()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_filtered_item(doctype, txt, searchfield, start, page_len, filters):
    if filters:
        bom = frappe.get_doc("BOM",filters.get('bom'))
        if bom.allow_adding_items:
            items = frappe.db.sql("select distinct name,item_name from `tabItem` where is_stock_item = 1 and disabled = 0")
            return items
        else:
            items = frappe.db.sql("""select distinct i.item_code,i.item_name from `tabBOM` as b inner join `tabBOM Item` as i on i.parent = b.name 
                        where allowed_to_change_qty_in_wo = 1""")
            return items