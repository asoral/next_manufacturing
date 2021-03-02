frappe.ui.form.on("Work Order",{
    onload: function(frm){
        if(frm.doc.docstatus == 4){
            frm.page.set_primary_action(__('Cancel'), () => {
                frm.savecancel(this);
            });
        }
    },
    refresh: function(frm){
        if(frm.doc.docstatus == 4){
            frm.page.set_primary_action(__('Cancel'), () => {
                frm.savecancel(this);
            });

            frm.trigger('show_progress_for_items');
			frm.trigger('show_progress_for_operations');

			frm.add_custom_button(__('Create Pick List'), function() {
                erpnext.work_order.create_pick_list(frm);
            });

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


            if(frm.doc.transfer_material_against != 'Job Card')
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
            if(frm.doc.status == 'In Process')
            {
                frm.add_custom_button(__('Material Produce'),function() {
                frappe.call({
                        method: "next_manufacturing.next_manufacturing.custom_work_order.make_material_produce",
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
        }
        if(frm.doc.docstatus == 1){
            frm.add_custom_button(__('Adjust Specific Gravity'),function() {
            });
            const show_start_btn = (frm.doc.skip_transfer || frm.doc.transfer_material_against == 'Job Card') ? 0 : 1;
            if (show_start_btn) {
                if ((flt(frm.doc.produced_qty) < flt(frm.doc.qty))
                    && frm.doc.status != 'Stopped') {
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

                                        if (r.message){
                                            var doclist = frappe.model.sync(r.message);
                                            frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
                                        }
                                    }
                                });
                            },
                            __('Additional Material'),
                            __("Add Additional Material")
                        );
                    });
                }
            }
        }
    },


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