// Copyright (c) 2021, Dexciss Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Consumption', {
    before_save: function(frm) {
        frm.clear_table('material_consumption_detail');
    },
    assign_material: function(frm){
        frappe.call({
            doc: frm.doc,
            method: "set_consume_material",
            callback: function(r) {
                frm.clear_table('material_consumption_detail');
                frm.reload_doc();
            }
        });
    },
    get_items_from_pick_list: function(frm){
        frappe.prompt(
            [
                {
                    fieldtype: "Link",
                    label: __("Pick List"),
                    options: "Pick List",
                    fieldname: "pick_list",
                    reqd:1,
                    get_query: () => {
                        return {
                            filters : {
                                "work_order": frm.doc.work_order,
                                "docstatus":1
                            }
                        }
                    }
                },
            ],
            function(data) {
                frm.call({
                    method: "next_manufacturing.next_manufacturing.doctype.material_consumption.material_consumption.add_pick_list_item",
                    args: {
                        doc_name: frm.doc.name,
                        pick_list:data.pick_list
                    },
                    callback: function(r){
                        frm.reload_doc()
                    }
                });
            },
            __('Get Pick List'),
            __("Add Pick List Item")
        );
    }
});

frappe.ui.form.on('Materials to Consume Items', {
    show_details: function(frm, cdt, cdn) {
        if (frm.doc.__islocal){
            frappe.throw(__("Please Save Material Consumption first!"))
        }
        var row = locals[cdt][cdn];
        get_available_qty_data(frm,row)
    },
});


function get_available_qty_data(frm,line_obj){
    frappe.call({
        method: "next_manufacturing.next_manufacturing.doctype.material_consumption.material_consumption.get_available_qty_data",
        args: {
            line_id: line_obj.name,
            company: frm.doc.company,
            item_code: line_obj.item_code,
            warehouse: line_obj.s_warehouse,
            has_batch_no:line_obj.has_batch_no,
            data:line_obj.data
        },
        callback: function (r) {
            if(r.message){
                frm.clear_table('material_consumption_detail');
                for (const d of r.message){
                    var row = frm.add_child('material_consumption_detail');
                    row.item = d.item_code;
                    row.uom = d.stock_uom;
                    row.warehouse = d.warehouse;
                    row.balance_qty = d.balance_qty;
                    row.consume_item = line_obj.name;
                    if(line_obj.has_batch_no == 1){
                        row.batch = d.batch_no;
                        row.expiry_date_batch = d.expiry_date;
                        row.life_left_batch = d.life_left_batch;
                    }
                    if(d.qty_to_consume){
                        row.qty_to_consume = d.qty_to_consume
                    }
                }
                frm.refresh_field('material_consumption_detail');
            }
        }
    });
}

