frappe.ui.form.on("Work Order",{
    refresh: function(frm){
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
                                    reqd:1
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
                                    fieldtype: "Currency",
                                    label: __("Rate"),
                                    fieldname: "rate",
                                    reqd:1
                                },
                            ],
                            function(data) {
                                frm.call({
                                    method: "next_manufacturing.next_manufacturing.custom_work_order.add_additional_fabric",
                                    args: {
                                        doc_name: frm.doc.name,
                                        item_code:data.item_code,
                                        required_qty:data.required_qty,
                                        rate:data.rate,
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