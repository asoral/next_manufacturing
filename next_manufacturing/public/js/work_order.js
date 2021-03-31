frappe.ui.form.on("Work Order", {
    refresh: function(frm){
        set_type(frm)
        set_line_data(frm)
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
            frm.add_custom_button(__('Produce Partial Qty'),function() {
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
            frm.add_custom_button(__('Complete Production'),function() {
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

function set_type(frm){
    var table = frm.doc.required_items
    table.map(item => {
        frappe.call({
            method: 'next_manufacturing.next_manufacturing.custom_work_order.get_type',
            args: {
                bom: frm.doc.bom_no,
                item_code: item.item_code
            },
            callback: function(resp){
                item.type = resp.message
            }
        })

    })
    frm.refresh_field("required_items")
}

function set_line_data(frm){
    var rm_weight = 0
    var fg_weight = 0
    var table = frm.doc.required_items
    table.map(item => {
        if(item.type === "RM"){
            rm_weight += item.consumed_qty * item.weight_per_unit 
        }
    })
    frm.set_value("rm_weight",rm_weight)
    var weight = produced_qty * weight_per_uom
    frm.set_value('fg_weight',weight )
    var yeild = (weight/rm_weight) * 100
    frm.set_value('yeild',yeild)
}