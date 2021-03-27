import frappe

@frappe.whitelist()
def get_item_data(item,wo):
    wo_source_warehouse = frappe.db.get_value("Work Order", {'name':wo}, ['rm_store_warehouse'])
    item_stock = frappe.db.get_value("Bin", {"warehouse": wo_source_warehouse,"item_code":item},['actual_qty'])
    q = """select item_name,weight_uom,weight_per_unit from `tabItem` where item_code='{0}'""".format(item)

    item_detail = frappe.db.sql(q, as_dict = True)
    data = []
    for i in item_detail:
        i['qty'] = item_stock
        data.append(i)
    return data


