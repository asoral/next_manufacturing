// Copyright (c) 2021, Dexciss Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Material request', {
	refresh: function(frm,cdt,cdn){
		frm.add_custom_button(__('Get Items'), function() {
			frappe.call({
				doc: frm.doc,
				method:"get_item_list",
				callback: function(resp){
					if(resp.message) {
						resp.message.map(item => {
							frm.add_child("items", {
								"item_code": item.item_code,
								'item_name': item.item_name,
								'item_group': item.item_group,
								'projected_qty_at_source_warehouse': item.projected_qty_at_source_warehouse,
								'actual_qty_at_source_warehouse' : item.actual_qty_at_source_warehouse,
								'required_qty': item.required_qty,
								'uom': item.uom,
								'qty_to_transfer': item.qty_to_transfer
							})
						})
						

					frm.refresh_field('items')
					}
					
				}
			})
		});
		  
	}
});
