from __future__ import unicode_literals
import frappe
from frappe import _


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
        mc.insert(ignore_permissions=True)
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