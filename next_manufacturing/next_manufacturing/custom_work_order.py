from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
import json

class StockOverProductionError(frappe.ValidationError): pass
class CustomWorkOrder(WorkOrder):
    def get_status(self, status=None):
        '''Return the status based on stock entries against this work order'''
        if not status:
            status = self.status

        if self.docstatus == 0:
            status = 'Draft'
        elif self.docstatus in [1,4]:
            if status != 'Stopped':
                stock_entries = frappe._dict(frappe.db.sql("""select purpose, sum(fg_completed_qty) from `tabStock Entry` where work_order=%s and docstatus=1 group by purpose""", self.name))
                status = "Not Started"
                if stock_entries:
                    status = "In Process"
                    produced_qty = stock_entries.get("Manufacture")
                    if flt(produced_qty) >= flt(self.qty):
                        status = "Completed"
        else:
            status = 'Cancelled'

        return status

    def update_work_order_qty(self):
        """Update **Manufactured Qty** and **Material Transferred for Qty** in Work Order
            based on Stock Entry"""

        allowance_percentage = flt(frappe.db.get_single_value("Manufacturing Settings",
                                                              "overproduction_percentage_for_work_order"))

        for purpose, fieldname in (("Manufacture", "produced_qty"),
                                   ("Material Transfer for Manufacture", "material_transferred_for_manufacturing")):
            if (purpose == 'Material Transfer for Manufacture' and
                    self.operations and self.transfer_material_against == 'Job Card'):
                continue

            qty = flt(frappe.db.sql("""select sum(fg_completed_qty) from `tabStock Entry` where work_order=%s and docstatus=1 and purpose=%s""", (self.name, purpose))[0][0])

            completed_qty = self.qty + (allowance_percentage / 100 * self.qty)
            # if qty > completed_qty:
            #     frappe.throw(_("{0} ({1}) cannot be greater than planned quantity ({2}) in Work Order {3}").format( \
            #         self.meta.get_label(fieldname), qty, completed_qty, self.name), StockOverProductionError)

            self.db_set(fieldname, qty)

            from erpnext.selling.doctype.sales_order.sales_order import update_produced_qty_in_so_item

            if self.sales_order and self.sales_order_item:
                update_produced_qty_in_so_item(self.sales_order, self.sales_order_item)

        if self.production_plan:
            self.update_production_plan_status()

    def update_required_items(self):
        '''
        update bin reserved_qty_for_production
        called from Stock Entry for production, after submit, cancel
        '''
        # calculate consumed qty based on submitted stock entries
        self.update_consumed_qty_for_required_items()

        if self.docstatus in [1, 4]:
            # calculate transferred qty based on submitted stock entries
            self.update_transaferred_qty_for_required_items()

            # update in bin
            self.update_reserved_qty_for_production()


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

def change_status(doc,mehtod):
    print("------------------")
    doc.docstatus = 4
    doc.flags.ignore_validate_update_after_submit = True
    doc.db_update()

@frappe.whitelist()
def add_additional_fabric(doc_name, item_code, required_qty):
    frappe.clear_cache()
    wo = frappe.get_doc("Work Order", doc_name)
    wo_line = frappe.get_list("Work Order Item", filters={"item_code": item_code, "parent": wo.name})
    if wo_line:
        woi_doc = frappe.get_doc("Work Order Item",wo_line[0].name)
        if woi_doc.required_qty:
            woi_doc.required_qty += float(required_qty)
            if woi_doc.rate:
                woi_doc.amount = woi_doc.required_qty * woi_doc.rate
        else:
            woi_doc.required_qty = required_qty
            if woi_doc.rate:
                woi_doc.amount = woi_doc.required_qty * woi_doc.rate
        woi_doc.flags.ignore_validate_update_after_submit = True
        woi_doc.save(ignore_permissions=True)
        wo.flags.ignore_validate_update_after_submit = True
        wo.validate()
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

    # stock_entry = frappe.new_doc("Stock Entry")
    # stock_entry.work_order = wo.name
    # stock_entry.stock_entry_type = "Material Transfer for Manufacture"
    # expense_account, cost_center = frappe.db.get_values("Company", wo.company, ["default_expense_account", "cost_center"])[0]
    # item_name, stock_uom, description = frappe.db.get_values("Item", item_code, ["item_name", "stock_uom", "description"])[0]
    #
    # item_expense_account, item_cost_center = frappe.db.get_value("Item Default", {'parent': item_code, 'company': wo.company}, ["expense_account", "buying_cost_center"])
    #
    # if not cost_center and not item_cost_center:
    #     frappe.throw(_("Please update default Cost Center for company {0}").format(wo.company))
    #
    # se_item = stock_entry.append("items")
    # se_item.item_code = item_code
    # se_item.qty = required_qty
    # se_item.s_warehouse = wo.source_warehouse
    # se_item.t_warehouse = wo.wip_warehouse
    # se_item.item_name = item_name
    # se_item.description = description
    # se_item.uom = stock_uom
    # se_item.stock_uom = stock_uom
    # se_item.expense_account = item_expense_account or expense_account
    # se_item.cost_center = item_cost_center or cost_center
    #
    # # in stock uom
    # se_item.conversion_factor = 1.00
    # stock_entry.set_actual_qty()
    # stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)
    #
    # return stock_entry.as_dict()
    return True


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


@frappe.whitelist()
def make_consume_material(doc_name):
    wo_doc = frappe.get_doc('Work Order',doc_name)
    mc = frappe.new_doc("Material Consumption")
    mc.work_order = wo_doc.name
    mc.t_warehouse = wo_doc.wip_warehouse
    mc.company = wo_doc.company
    mc.type = "Manual"
    for res in wo_doc.required_items:
        item_doc = frappe.get_doc("Item",res.item_code)
        mc.append("materials_to_consume", {
            "item_code": res.item_code,
            "item_name": res.item_name,
            "s_warehouse": res.source_warehouse,
            "has_batch_no": item_doc.has_batch_no,
            "uom": item_doc.stock_uom,
            "status": "Not Assigned",
            "qty_to_issue": res.required_qty
        })
    mc.insert(ignore_permissions=True)
    return mc.as_dict()


@frappe.whitelist()
def create_pick_list(source_name, target_doc=None, for_qty=None):
    for_qty = for_qty or json.loads(target_doc).get('for_qty')
    max_finished_goods_qty = frappe.db.get_value('Work Order', source_name, 'qty')
    def update_item_quantity(source, target, source_parent):
        pending_to_issue = flt(source.required_qty) - flt(source.transferred_qty)
        desire_to_transfer = flt(source.required_qty) / max_finished_goods_qty * flt(for_qty)

        qty = 0
        if desire_to_transfer <= pending_to_issue:
            qty = desire_to_transfer
        elif pending_to_issue > 0:
            qty = pending_to_issue

        if qty:
            target.qty = qty
            target.stock_qty = qty
            target.uom = frappe.get_value('Item', source.item_code, 'stock_uom')
            target.stock_uom = target.uom
            target.conversion_factor = 1
        else:
            target.delete()

    doc = get_mapped_doc('Work Order', source_name, {
        'Work Order': {
            'doctype': 'Pick List',
            'validation': {
                'docstatus': ['in', [1, 4]]
            }
        },
        'Work Order Item': {
            'doctype': 'Pick List Item',
            'postprocess': update_item_quantity,
            'condition': lambda doc: abs(doc.transferred_qty) < abs(doc.required_qty)
        },
    }, target_doc)
    doc.for_qty = for_qty
    doc.set_item_locations()
    return doc

@frappe.whitelist()
def make_material_produce(doc_name,partial=0):
    wo_doc = frappe.get_doc('Work Order', doc_name)
    bom = frappe.get_doc('BOM', wo_doc.bom_no)
    mc = frappe.new_doc("Material Produce")
    mc.work_order = wo_doc.name
    mc.bom = bom.name
    mc.batch_size = bom.batch_size
    mc.partial_produce = partial
    mc.t_warehouse = wo_doc.fg_warehouse
    mc.company = wo_doc.company
    item_doc = frappe.get_doc("Item", wo_doc.production_item)
    mc.append("material_produce_item", {
        "item_code": wo_doc.production_item,
        "item_name": wo_doc.item_name,
        "item_group": item_doc.item_group,
        "s_warehouse": wo_doc.fg_warehouse,
        "uom": item_doc.stock_uom,
        "status": "Not Set",
        "type": "FG",
        "scheduled_qty": wo_doc.qty,
        "qty_produced": wo_doc.qty - wo_doc.produced_qty,
        "qty_already_produced": wo_doc.produced_qty
    })

    bom = frappe.get_doc("BOM",wo_doc.bom_no)
    for res in bom.scrap_items:
        item_doc = frappe.get_doc("Item", res.item_code)
        mc.append("material_produce_item", {
            "item_code": res.item_code,
            "item_name": item_doc.item_name,
            "item_group": item_doc.item_group,
            "s_warehouse": wo_doc.wip_warehouse,
            "uom": res.stock_uom,
            "status": "Not Set",
            "type": "Scrap",
            "scheduled_qty": res.stock_qty
        })
    mc.insert(ignore_permissions=True)
    return mc.as_dict()