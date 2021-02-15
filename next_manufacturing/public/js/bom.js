frappe.ui.form.on("BOM",{
    before_save:function(frm){
        frm.trigger("set_specific_gravity");

    },

    set_specific_gravity: function(frm){
        //total weight
        $.each(frm.doc["items"],function(i, items){
                if(items.specific_gravity){
                    items.total_quantity = items.stock_qty * items.weight_per_unit;
                }
         });

        //specific gravity
        var cnt = 0.0;
        var sg = 0.0;
        $.each(frm.doc["items"],function(i, items)
                {
                    if(items.specific_gravity){
                        cnt += 1;
                        sg += items.specific_gravity;
                }
         });
         var sg_avg = sg/cnt;
         frm.set_value("specific_gravity",sg_avg);

        //raw material weight
        var rmw = 0.0;
        $.each(frm.doc["items"],function(i, items)
                {
                    if(items.stock_qty && items.type == "RM"){
                        rmw += items.stock_qty * items.weight_per_unit;
                }
         });
         frm.set_value("rm_weight",rmw);

        //bom weight
        var bmw = 0.0;
        $.each(frm.doc["items"],function(i, items)
                {
                    if(items.stock_qty){
                        bmw += items.stock_qty * items.weight_per_unit;
                }
         });
        frm.set_value("bom_weight",bmw);

        // Finish Good Weight
        frm.set_value("fg_weight",frm.doc.weight_per_unit * frm.doc.quantity);

        // yeild value
        frm.set_value("yeild",((frm.doc.fg_weight/frm.doc.rm_weight) * 100))
    },
});

//cur_frm.cscript.update_totals = function(doc) {
//	var td=0.0; var tc =0.0;
//	var items = doc.items || [];
//	for(var i in items) {
//		td = flt(items[i].stock_qty) * flt(items[i].weight_per_unit);
//		d.
//	}
//	var doc = locals[doc.doctype][doc.name];
//	doc.total_debit = td;
//	doc.total_credit = tc;
//	doc.difference = flt((td - tc), precision("difference"));
//	refresh_many(['total_debit','total_credit','difference']);
//}

//frappe.ui.form.on("BOM Item", "uom", function(frm, cdt, cdn) {
//	var d = locals[cdt][cdn];
//	cur_frm.cscript.update_totals(frm.doc);
//
//});
//frappe.ui.form.on("BOM Item", "qty", function(frm, cdt, cdn) {
//	var d = locals[cdt][cdn];
//	cur_frm.cscript.update_totals(frm.doc);
//    var total_weight = d.stock_qty * d.weight_per_unit;
//    console.log("totalwe",total_weight);
//    frappe.model.set_value(cdt,cdn,"total_weight",total_weight);
//    refresh_many(['total_weight']);
//});
