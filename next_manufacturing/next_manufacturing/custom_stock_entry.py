from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.model.naming import make_autoname
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from erpnext.stock.doctype.batch.batch import set_batch_nos

class CustomStockEntry(StockEntry):
    def validate(self):
        self.pro_doc = frappe._dict()
        if self.work_order:
            self.pro_doc = frappe.get_doc('Work Order', self.work_order)

        self.validate_posting_time()
        self.validate_purpose()
        self.validate_item()
        self.validate_customer_provided_item()
        self.validate_qty()
        self.set_transfer_qty()
        self.validate_uom_is_integer("uom", "qty")
        self.validate_uom_is_integer("stock_uom", "transfer_qty")
        self.validate_warehouse()
        self.validate_work_order()
        self.validate_bom()
        self.mark_finished_and_scrap_items()
        self.validate_finished_goods()
        self.validate_with_material_request()
        self.validate_batch()
        self.validate_inspection()
        self.validate_fg_completed_qty()
        self.validate_difference_account()
        self.set_job_card_data()
        self.set_purpose_for_stock_entry()

        if not self.from_bom:
            self.fg_completed_qty = 0.0

        if self._action == 'submit':
            self.make_batches('t_warehouse')
        else:
            set_batch_nos(self, 's_warehouse')

        self.validate_serialized_batch()
        self.set_actual_qty()
        self.calculate_rate_and_amount()
        self.validate_putaway_capacity()

    #custom method
    def make_batches(self, warehouse_field):
        '''Create batches if required. Called before submit'''
        enabled = frappe.db.get_single_value('Batch Settings', 'enabled')
        is_finish_batch_series = frappe.db.get_single_value('Batch Settings', 'is_finish_batch_series')
        batch_series = frappe.db.get_single_value('Batch Settings', 'batch_series')
        for d in self.items:
            if d.get(warehouse_field) and not d.batch_no:
                has_batch_no, create_new_batch = frappe.db.get_value('Item', d.item_code,
                                                                     ['has_batch_no', 'create_new_batch'])
                if has_batch_no and create_new_batch:
                    batch_name = None
                    if self.work_order:
                        if enabled:
                            if is_finish_batch_series == 'Use Work Order as Series':
                                batch_name = make_autoname(str(self.work_order) + "-.##")
                            if is_finish_batch_series == 'Create New':
                                batch_name = make_autoname(batch_series)

                    d.batch_no = frappe.get_doc(dict(
                        doctype='Batch',
                        batch_id=batch_name,
                        item=d.item_code,
                        supplier=getattr(self, 'supplier', None),
                        reference_doctype=self.doctype,
                        reference_name=self.name)).insert().name