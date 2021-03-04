frappe.ui.form.on("Job Card",{
    refresh: function(frm){
        if (frm.doc.status != 'Completed'){
            frm.add_custom_button(__('Consume Material'),function() {
                frappe.call({
                    method: "next_manufacturing.next_manufacturing.custom_job_card.make_material_consumption",
                    args: {
                      doc_name: frm.doc.name
                    },
                    callback: function(r){
                        if (r.message) {
                            var doc = frappe.model.sync(r.message)[0];
                            frappe.set_route("Form", doc.doctype, doc.name);
                        }
                    }
                });
            }).addClass('btn-primary');

            frm.add_custom_button(__('Add Additional Material'), function() {
                frappe.prompt(
                    [
                        {
                            fieldtype: "Link",
                            label: __("Item"),
                            options: "Item",
                            fieldname: "item_code",
                            reqd:1,
                            get_query: () => {
                                return {
                                    query: "next_manufacturing.next_manufacturing.custom_work_order.get_filtered_item",
                                    filters : {
                                        "is_stock_item": 1,
                                        "bom": frm.doc.bom_no
                                    }
                                }
                            }
                        },
                        {
                            "fieldtype": "Column Break"
                        },
                        {
                            fieldtype: "Float",
                            label: __("Required Qty"),
                            fieldname: "required_qty",
                            reqd:1
                        },
                        {
                            "fieldtype": "Column Break"
                        },
                        {
                            fieldtype: "Link",
                            label: __("Warehouse"),
                            fieldname: "warehouse",
                            options: "Warehouse",
                            get_query: () => {
                                return {
                                    filters : {
                                        "company": frm.doc.company
                                    }
                                }
                            }
                        }
                    ],
                    function(data) {
                        frm.call({
                            method: "next_manufacturing.next_manufacturing.custom_job_card.add_additional_fabric_in_job_card",
                            args: {
                                doc_name: frm.doc.name,
                                item_code:data.item_code,
                                required_qty:data.required_qty,
                                warehouse:data.warehouse
                            },
                            callback: function(r){
                                frm.reload_doc()
                            }
                        });
                    },
                    __('Additional Material'),
                    __("Add Additional Material")
                );
            });
        }
    }
});