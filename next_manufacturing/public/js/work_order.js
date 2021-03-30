frappe.ui.form.on("Work Order",{
    onload: function(frm){
        if(frm.doc.custom_status == 1){
            frm.page.set_primary_action(__('Cancel'), () => {
                frm.savecancel(this);
            });
        }
        if(frm.doc.docstatus == 1){
            if (frm.custom_buttons) frm.clear_custom_buttons();
        }

    },
    refresh: function(frm){
        frm.set_query('rm_cost_center', function() {
			return {
				filters: {
					'company': frm.doc.company
				}
			};
		});
        frm.set_query('rm_store_warehouse', function() {
			return {
				filters: {
					'company': frm.doc.company
				}
			};
		});
        frm.set_query('fg_store_warehouse', function() {
			return {
				filters: {
					'company': frm.doc.company
				}
			};
		});


        if(frm.doc.custom_status == 1){
            frm.page.set_primary_action(__('Cancel'), () => {
                frm.savecancel(this);
            });

            frm.trigger('show_progress_for_items');
			frm.trigger('show_progress_for_operations');


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
                frappe.call({
                    method:'next_manufacturing.next_manufacturing.custom_work_order.show_btn', 
                    args: {
                        "bom": frm.doc.bom_no
                    },
                    callback: function(resp){
                        if(resp.message === true){
                            frm.add_custom_button(__('Add Additional Material'), function() {
                                frappe.new_doc("Additional Items", {"work_order" : frm.doc.name, "user": frappe.session.user, 'date': frappe.datetime.now_date()})
                                
                            });
                        }
                    }
                })
                // frm.add_custom_button(__('Add Additional Material'), function() {
                //     frappe.new_doc("Additional Items", {"work_order" : frm.doc.name, "user": frappe.session.user, 'date': frappe.datetime.now_date()})
                    
                // });
            }
            if(frm.doc.status != "Completed"){
                frm.add_custom_button(__('Create Pick List'), function() {
                    erpnext.work_order.create_pick_list(frm);
                }, __('Create'));
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
                        frm.trigger("make_job_cards");
                    }, __('Create'));
                }
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
        if(frm.doc.docstatus == 1){
            if (frm.custom_buttons) frm.clear_custom_buttons();
        }
        if(!frm.doc.__islocal && frm.doc.docstatus != 2){
            if(frm.doc.transfer_material_against != 'Job Card' || frm.doc.status == "Completed"){
                frm.add_custom_button(__('Material Request'), function() {
                    make_material_request(frm,frm.doc.status)
                }, __('Create'));
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
        if(!frm.doc.__islocal){
            frm.add_custom_button(__("Print"), function() {
                frm.print_doc();
            }).addClass('btn-danger');
        }
    },
    make_job_cards: function(frm) {
		let qty = 0;
		let operations_data = [];

		const dialog = frappe.prompt({fieldname: 'operations', fieldtype: 'Table', label: __('Operations'),
			fields: [
				{
					fieldtype:'Link',
					fieldname:'operation',
					label: __('Operation'),
					read_only:1,
					in_list_view:1
				},
				{
					fieldtype:'Link',
					fieldname:'workstation',
					label: __('Workstation'),
					read_only:1,
					in_list_view:1
				},
				{
					fieldtype:'Data',
					fieldname:'name',
					label: __('Operation Id')
				},
				{
					fieldtype:'Float',
					fieldname:'pending_qty',
					label: __('Pending Qty'),
				},
				{
					fieldtype:'Float',
					fieldname:'qty',
					label: __('Quantity to Manufacture'),
					read_only:0,
					in_list_view:1,
				},
			],
			data: operations_data,
			in_place_edit: true,
			get_data: function() {
				return operations_data;
			}
		}, function(data) {
			frappe.call({
				method: "erpnext.manufacturing.doctype.work_order.work_order.make_job_card",
				args: {
					work_order: frm.doc.name,
					operations: data.operations,
				},
				callback: function(r){
				    frm.reload_doc();
				}
			});
		}, __("Job Card"), __("Create"));

		dialog.fields_dict["operations"].grid.wrapper.find('.grid-add-row').hide();

		var pending_qty = 0;
		frm.doc.operations.forEach(data => {
			if(data.completed_qty != frm.doc.qty) {
				pending_qty = frm.doc.qty - flt(data.completed_qty);

				dialog.fields_dict.operations.df.data.push({
					'name': data.name,
					'operation': data.operation,
					'workstation': data.workstation,
					'qty': pending_qty,
					'pending_qty': pending_qty,
				});
			}
		});
		dialog.fields_dict.operations.grid.refresh();

	},
});

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