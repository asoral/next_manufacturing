frappe.ui.form.on("Stock Entry", {
    onload: function(frm,cdt,cdn){
       
        set_qty_to_se(frm,cdt,cdn)
    },
    refresh: function(frm,cdt,cdn){
        set_qty_to_se(frm,cdt,cdn)
    }
})

function set_qty_to_se(frm,cdt,cdn){
    // frappe.call({
    //     method: "next_manufacturing.api.set_qty",
    //     args: {
    //         table: frm.doc.items
    //     },
    //     callback: function(resp){
    //         if(resp.message){
    //             if(frm.doc.docstatus === 0 && frm.doc.stock_entry_type === "Material Transfer for Manufacture") {
    //                 frm.doc.fg_completed_qty = resp.message
    //                 frm.refresh_field('fg_completed_qty')
    //             }
                
    //         }
    //     }
    // })
}