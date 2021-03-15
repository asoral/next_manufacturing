frappe.ui.form.on("Work Order",{
    onload: function(frm){
        if(frm.doc.docstatus == 4){
            frm.page.set_primary_action(__('Cancel'), () => {
                frm.savecancel(this);
            });
        }
    },
    refresh: function(frm){
        if(!frm.doc.__islocal && frm.doc.docstatus != 2){
            frm.add_custom_button(__('Material Request'), function() {
                make_material_request(frm,frm.doc.status)
            }).addClass('btn-primary');
        }

        if(frm.doc.docstatus == 4){
            frm.page.set_primary_action(__('Cancel'), () => {
                frm.savecancel(this);
            });

            frm.trigger('show_progress_for_items');
			frm.trigger('show_progress_for_operations');
            if(frm.doc.status != "Completed"){
                frm.add_custom_button(__('Create Pick List'), function() {
                    erpnext.work_order.create_pick_list(frm);
                });
            }
            if(frm.doc.operations && frm.doc.operations.length
			&& frm.doc.qty != frm.doc.material_transferred_for_manufacturing)
			{
			    const not_completed = frm.doc.operations.filter(d => {
				if(d.status != 'Completed') {
                        return true;
                    }
                });

                if(not_completed && not_completed.length) {
                    frm.add_custom_button(__('Create Job Card'), () => {
                        frm.trigger("make_job_card");
                    }).addClass('btn-primary');
                }
			}

            if(frm.doc.transfer_material_against != 'Job Card' && frm.doc.status != "Completed")
            {
                frm.add_custom_button(__('Consume Material'),function() {
                frappe.call({
                        method: "next_manufacturing.next_manufacturing.custom_work_order.make_consume_material",
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
            }
            if(frm.doc.transfer_material_against != 'Job Card' && frm.doc.status == 'In Process')
            {
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
                            }
                        ],
                        function(data) {
                            frm.call({
                                method: "next_manufacturing.next_manufacturing.custom_work_order.add_additional_fabric",
                                args: {
                                    doc_name: frm.doc.name,
                                    item_code:data.item_code,
                                    required_qty:data.required_qty,
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
            if (frm.doc.status == 'In Process')
            {
                frm.add_custom_button(__('Partial'),function() {
                frappe.call({
                        method: "next_manufacturing.next_manufacturing.custom_work_order.make_material_produce",
                        args: {
                          doc_name: frm.doc.name,
                          partial: 1
                        },
                        callback: function(r){
                            if (r.message) {
                                var doc = frappe.model.sync(r.message)[0];
                                frappe.set_route("Form", doc.doctype, doc.name);
                            }
                        }
                    });
                }, __('Produce'));

                frm.add_custom_button(__('Complete'),function() {
                frappe.call({
                        method: "next_manufacturing.next_manufacturing.custom_work_order.make_material_produce",
                        args: {
                          doc_name: frm.doc.name,
                          partial: 0
                        },
                        callback: function(r){
                            if (r.message) {
                                var doc = frappe.model.sync(r.message)[0];
                                frappe.set_route("Form", doc.doctype, doc.name);
                            }
                        }
                    });
                }, __('Produce'));
            }
        }
        if(!frm.doc.__islocal){
            frappe.call({
                method: "next_manufacturing.next_manufacturing.custom_work_order.set_operation_rm_cost",
                args: {
                    doc_name: frm.doc.name,
                    bom_no: frm.doc.bom_no,
                    transfer_material_against: frm.doc.transfer_material_against
                },
                callback: function(r){
                    frm.refresh_field("planned_rm_cost")
                }
            });
        }
    }


//    before_save: function(frm){
//        if(frm.doc.docstatus != 1 && frm.doc.__islocal != 1){
//            frm.call({
//                'method': "next_manufacturing.next_manufacturing.custom_work_order.after_save",
//                "args": {
//                    doc_name: frm.doc.name
//                },
//                "callback": function(r){
//                }
//                })
//            refresh_many(['rm_weight','fg_weight','bom_weight','specific_gravity']);
//        }
//    },

//    set_specific_gravity_2: function(frm){
//         //raw material weight
//        var rmw = 0.0;
//        $.each(frm.doc["required_items"],function(i, required_items)
//                {
//                    if(required_items.stock_qty && items.type == "RM"){
//                        rmw += items.stock_qty;
//                }
//         });
//         frm.set_value("rm_weight",rmw);
//
//        //bom weight
//        var bmw = 0.0;
//        $.each(frm.doc["items"],function(i, items)
//                {
//                    if(items.stock_qty){
//                        bmw += items.stock_qty;
//                }
//         });
//        frm.set_value("bom_weight",bmw);
//    },
});

function make_material_request(frm,status){
    let fields =  [
        {
            fieldtype: "Link",
            label: __("Source Warehouse"),
            options: "Warehouse",
            fieldname: "warehouse",
            reqd:1,
            get_query: () => {
                return {
                    filters : {
                        "company": frm.doc.company
                    }
                }
            }
        }
    ]
    if(status == "Completed"){
        fields =  [
            {
                fieldtype: "Link",
                label: __("Target Warehouse"),
                options: "Warehouse",
                fieldname: "warehouse",
                reqd:1,
                get_query: () => {
                    return {
                        filters : {
                            "company": frm.doc.company
                        }
                    }
                }
            }
        ]
    }
    frappe.prompt(
        fields,
        function(data) {
            frm.call({
                method: "next_manufacturing.next_manufacturing.custom_work_order.make_material_request",
                args: {
                    doc_name: frm.doc.name,
                    warehouse:data.warehouse,
                    status:status
                },
                callback: function(r){
                    if (r.message) {
                        var doc = frappe.model.sync(r.message)[0];
                        frappe.set_route("Form", doc.doctype, doc.name);
                    }
                }
            });
        },
        __('Material Request'),
        __("Make Additional Material")
    );
}