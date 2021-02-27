frappe.ui.form.on("Job Card",{
    refresh: function(frm){
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
    }
});