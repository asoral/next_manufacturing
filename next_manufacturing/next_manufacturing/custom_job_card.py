from __future__ import unicode_literals
import frappe


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