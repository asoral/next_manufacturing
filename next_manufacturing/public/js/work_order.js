frappe.ui.form.on("Work Order", {
    refresh: function(frm){
        frm.remove_custom_button("Start")
        frm.remove_custom_button("Create Pick List")
        cur_frm.page.get_inner_group_button(__("Status")).find("button").addClass("hide");
        //cur_frm.page.get_inner_group_button(__("Create Pick List")).find("button").addClass("hide");
        if(frm.doc.status == "Submitted" || frm.doc.status == "In Process"){
            frm.add_custom_button(__('Material Request'),function() {
                make_material_request(frm,frm.doc.status)
            }, __('Functions'))
        }
        if(frm.doc.status == "Submitted" || frm.doc.status == "Not Started" || frm.doc.status == "In Process"){
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
            }, __('Functions'))
            frm.add_custom_button(__('Create Pick List'),function() {
                erpnext.work_order.create_pick_list(frm);
            }, __('Functions'))

        }
        if(frm.doc.status == "In Process"){
            frm.add_custom_button(__('Add Additional Items'),function() {
                console.log('****', frappe.session.user)
                console.log(frappe.datetime.now_date())
                var usr = frappe.session.user
                frappe.new_doc("Additional Items", {"work_order" : frm.doc.name, "user": usr, 'date': frappe.datetime.now_date()})
            }, __('Functions'))
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
            }, __('Functions'))
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
            }, __('Functions'))
        }
        
    }
})

function make_material_request(frm,status){
    frm.call({
        method: "next_manufacturing.next_manufacturing.custom_work_order.make_material_request",
        args: {
            doc_name: frm.doc.name,
            status:status
        },
        callback: function(r){
            if (r.message) {
                var doc = frappe.model.sync(r.message)[0];
                frappe.set_route("Form", doc.doctype, doc.name);
            }
        }
    });
}