frappe.ui.form.on("Work Order",{
    refresh: function(frm){
        if(frm.doc.docstatus == 1){
            frm.add_custom_button(__('Adjust Specific Gravity'),function() {
            });
        }
    },

    after_save: function(frm){
        if(frm.doc.docstatus != 1){
            frm.call({
                'method': "next_manufacturing.next_manufacturing.custom_work_order.after_save",
                "args": {
                    doc_name: frm.doc.name
                },
                "callback": function(r){
                }
                })
            refresh_many(['rm_weight','fg_weight','bom_weight','specific_gravity']);
        }
    },

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