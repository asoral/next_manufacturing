from __future__ import unicode_literals
import frappe
from frappe import _,bold
from erpnext.manufacturing.doctype.job_card.job_card import JobCard
from frappe.utils import (flt, cint, time_diff_in_hours, get_datetime, get_link_to_form)
from frappe.model.mapper import get_mapped_doc

class OverlapError(frappe.ValidationError): pass

class CustomJobCard(JobCard):
    def validate(self):
        print("*********************")
        if self.time_logs:
            for time in self.time_logs:
                #print(time.get("completed_qty"))
                time.completed_qty = self.for_quantity
    
    def before_submit(self):
        self.status = 'Completed'

    def validate_job_card(self):
        if not self.time_logs:
            frappe.throw(_("Time logs are required for {0} {1}")
                         .format(bold("Job Card"), get_link_to_form("Job Card", self.name)))

        # if self.for_quantity and self.total_completed_qty != self.for_quantity:
        #     total_completed_qty = bold(_("Total Completed Qty"))
        #     qty_to_manufacture = bold(_("Qty to Manufacture"))
        #
        #     frappe.throw(_("The {0} ({1}) must be equal to {2} ({3})")
        #                  .format(total_completed_qty, bold(self.total_completed_qty), qty_to_manufacture,
        #                          bold(self.for_quantity)))

    def set_status(self, update_status=False):
        if self.status == "On Hold": return

        self.status = {
            0: "Open",
            1: "Submitted",
            2: "Cancelled"
        }[self.docstatus or 0]
        if self.time_logs:
                self.status = 'Work In Progress'
                wo = frappe.get_doc("Work Order", self.work_order)
                if wo.status == "Not Started":
                    wo.status = "In Process"
                    wo.db_update()

        if (self.docstatus == 1 and
                (self.for_quantity <= self.transferred_qty or not self.items)):
            self.status = 'Completed'

        if self.status != 'Completed':
            if self.for_quantity <= self.transferred_qty:
                self.status = 'Material Transferred'

        if update_status:
            self.db_set('status', self.status)

    def validate_time_logs(self):
        self.total_completed_qty = 0.0
        self.total_time_in_mins = 0.0

        if self.get('time_logs'):
            for d in self.get('time_logs'):
                if not d.pre_planning:
                    if get_datetime(d.from_time) > get_datetime(d.to_time):
                        frappe.throw(_("Row {0}: From time must be less than to time").format(d.idx))

                    data = self.get_overlap_for(d)
                    if data:
                        frappe.throw(_("Row {0}: From Time and To Time of {1} is overlapping with {2}")
                                     .format(d.idx, self.name, data.name), OverlapError)

                    if d.from_time and d.to_time:
                        d.time_in_mins = time_diff_in_hours(d.to_time, d.from_time) * 60
                        self.total_time_in_mins += d.time_in_mins

                if d.completed_qty:
                    self.total_completed_qty += d.completed_qty

    def update_work_order_data(self, for_quantity, time_in_mins, wo):
        time_data = frappe.db.sql("""
            SELECT
                min(from_time) as start_time, max(to_time) as end_time
            FROM `tabJob Card` jc, `tabJob Card Time Log` jctl
            WHERE
                jctl.parent = jc.name and jc.work_order = %s
                and jc.operation_id = %s and jc.docstatus = 1 and jctl.pre_planning = 0
            """, (self.work_order, self.operation_id), as_dict=1)
        for data in wo.operations:
            if data.get("name") == self.operation_id:
                data.completed_qty = for_quantity
                data.actual_operation_time = time_in_mins
                data.actual_start_time = time_data[0].start_time if time_data else None
                data.actual_end_time = time_data[0].end_time if time_data else None

        wo.flags.ignore_validate_update_after_submit = True
        wo.update_operation_status()
        wo.calculate_operating_cost()
        wo.set_actual_dates()
        wo.save()

@frappe.whitelist()
def make_material_consumption(doc_name):
    job = frappe.get_doc("Job Card", doc_name)
    if job:
        mc = frappe.new_doc("Material Consumption")
        mc.work_order = job.work_order
        mc.job_card = job.name
        mc.t_warehouse = job.wip_warehouse
        mc.company = job.company
        mc.type = "Manual"
        for res in job.items:
            item_doc = frappe.get_doc("Item", res.item_code)
            mc.append("materials_to_consume", {
                "item_code": res.item_code,
                "item_name": res.item_name,
                "s_warehouse": res.source_warehouse,
                "has_batch_no": item_doc.has_batch_no,
                "uom": item_doc.stock_uom,
                "status": "Not Assigned",
                "qty_to_issue": res.required_qty
            })
        # mc.insert(ignore_permissions=True)
        return mc.as_dict()

@frappe.whitelist()
def add_additional_fabric_in_job_card(doc_name, item_code, required_qty, warehouse= None):
    job = frappe.get_doc("Job Card", doc_name)
    wo_line = frappe.get_list("Job Card Item", filters={"item_code": item_code, "parent": job.name})
    if wo_line:
        jci_doc = frappe.get_doc("Job Card Item", wo_line[0].name)
        if jci_doc.required_qty:
            jci_doc.required_qty += float(required_qty)
        else:
            jci_doc.required_qty = required_qty
        jci_doc.flags.ignore_validate_update_after_submit = True
        jci_doc.save(ignore_permissions=True)
        job.flags.ignore_validate_update_after_submit = True
        job.validate()
    else:
        if not warehouse:
            frappe.throw(_("Please select Warehouse!"))

        item = frappe.get_doc("Item", item_code)
        job.append("items", {
            "item_code": item_code,
            "item_name": item.item_name,
            "description": item.description,
            "source_warehouse": warehouse,
            "uom": item.stock_uom,
            "required_qty": required_qty
        })
        job.flags.ignore_validate_update_after_submit = True
        job.save(ignore_permissions=True)

    if job.work_order:
        from next_manufacturing.next_manufacturing.custom_work_order import add_additional_fabric
        add_additional_fabric(job.work_order, item_code, required_qty, warehouse)
    return True

@frappe.whitelist()
def change_status_to_wo(wo,status):
    if status == 'Work In Progress':
        print('yes')
        q = """update `tabWork Order` set status = 'In Process' where name = '{0}';""".format(wo)
        print(q)
        frappe.db.sql(q)
        frappe.db.commit()
        print('ok')

def status_job_card_status(doc, method):
    doc.status = "Open"
    doc.db_update()

def set_pre_planning_line(doc, method):
    if doc.time_logs:
        for res in doc.time_logs:
            res.pre_planning = 1

def transferred_qty_validate(doc, method):
    if not doc.transferred_qty:
        frappe.throw(_("Consume Material Qty should be greater than Zero. Please Consume Material first!"))

@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
    def update_item(obj, target, source_parent):
        target.warehouse = source_parent.wip_warehouse

    def set_missing_values(source, target):
        target.material_request_type = "Material Transfer"
        wo = frappe.get_doc("Work Order", source.work_order)
        target.material_request_type = "Material Transfer"
        target.set_from_warehouse = wo.rm_store_warehouse

    doclist = get_mapped_doc("Job Card", source_name, {
        "Job Card": {
            "doctype": "Material Request",
            "field_map": {
                "name": "job_card",
                "work_order": "work_order",
            },
        },
        "Job Card Item": {
            "doctype": "Material Request Item",
            "field_map": {
                "required_qty": "qty",
                "uom": "stock_uom"
            },
            "postprocess": update_item,
        }
    }, target_doc, set_missing_values)

    return doclist
