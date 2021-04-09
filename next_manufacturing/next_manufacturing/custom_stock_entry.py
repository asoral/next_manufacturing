from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.model.naming import make_autoname
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from erpnext.stock.doctype.batch.batch import set_batch_nos
from frappe.utils import flt
from frappe import _

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
    
    #custom code
    def set_stock_entry_type(self):
        mr = frappe.db.get_value("Pick", {"name":self.pick_list}, ['material_request'])
        material_transfer_to_mfg = frappe.db.get_value("Material Request",{'name':mr}, ['material_transfer_to_mfg'])                                         
        if self.purpose and material_transfer_to_mfg == 0:
            self.stock_entry_type = frappe.get_cached_value('Stock Entry Type',{'purpose': self.purpose}, 'name')
        if self.purpose and material_transfer_to_mfg == 1:
            self.stock_entry_type = "Material Transfer"
    #custom method
    def make_batches(self, warehouse_field):
        '''Create batches if required. Called before submit'''
        enabled = frappe.db.get_single_value('Batch Settings', 'enabled')
        if enabled:
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
        else:
            super(CustomStockEntry, self).make_batches(warehouse_field)

    def get_items(self):
        super(CustomStockEntry, self).get_items()
        if self.purpose == "Manufacture":
            wo = frappe.get_doc("Work Order",self.work_order)
            wo_lines = frappe.get_list("Work Order Item",filters={"parent": self.work_order, "additional_material":1},fields=['name'], as_list=1)
            for res in wo_lines:
                wo_line_doc = frappe.get_doc("Work Order Item",res[0])
                expense_account, cost_center = frappe.db.get_values("Company", wo.company, ["default_expense_account", "cost_center"])[0]
                item_name, stock_uom, description = frappe.db.get_values("Item", wo_line_doc.item_code, ["item_name", "stock_uom", "description"])[0]

                item_expense_account, item_cost_center = frappe.db.get_value("Item Default",{'parent': wo_line_doc.item_code, 'company': wo.company},
                                                                             ["expense_account", "buying_cost_center"])

                se_child = self.append('items')
                se_child.s_warehouse = wo.wip_warehouse
                se_child.item_code = wo_line_doc.item_code
                se_child.uom = stock_uom
                se_child.stock_uom = stock_uom
                se_child.basic_rate = wo_line_doc.rate
                se_child.qty = wo_line_doc.transferred_qty
                se_child.allow_alternative_item = wo_line_doc.allow_alternative_item
                se_child.cost_center = item_cost_center or cost_center
                se_child.is_scrap_item = 0

                for field in ["idx", "po_detail", "original_item",
                              "expense_account", "description", "item_name"]:
                    if wo_line_doc.get(field):
                        se_child.set(field, wo_line_doc.get(field))
                # in stock uom
                se_child.conversion_factor = 1
                se_child.transfer_qty = flt(wo_line_doc.transferred_qty * se_child.conversion_factor, se_child.precision("qty"))
                self.set_actual_qty()
                self.calculate_rate_and_amount(raise_error_if_no_rate=False)

    def update_work_order(self):
        def _validate_work_order(pro_doc):
            if flt(pro_doc.docstatus) not in [1, 4]:
                frappe.throw(_("Work Order {0} must be submitted").format(self.work_order))

            if pro_doc.status == 'Stopped':
                frappe.throw(_("Transaction not allowed against stopped Work Order {0}").format(self.work_order))

        if self.job_card:
            job_doc = frappe.get_doc('Job Card', self.job_card)
            job_doc.set_transferred_qty(update_status=True)

        if self.work_order:
            pro_doc = frappe.get_doc("Work Order", self.work_order)
            _validate_work_order(pro_doc)
            pro_doc.run_method("update_status")

            if self.fg_completed_qty:
                pro_doc.run_method("update_work_order_qty")
                if self.purpose == "Manufacture":
                    pro_doc.run_method("update_planned_qty")

            if not pro_doc.operations:
                pro_doc.set_actual_dates()

    def check_if_operations_completed(self):
        """Check if Time Sheets are completed against before manufacturing to capture operating costs."""
        prod_order = frappe.get_doc("Work Order", self.work_order)
        allowance_percentage = flt(frappe.db.get_single_value("Manufacturing Settings",
                                                              "overproduction_percentage_for_work_order"))

        for d in prod_order.get("operations"):
            total_completed_qty = flt(self.fg_completed_qty) + flt(prod_order.produced_qty)
            completed_qty = d.completed_qty + (allowance_percentage / 100 * d.completed_qty)
            if total_completed_qty > flt(completed_qty):
                job_card = frappe.db.get_value('Job Card', {'operation_id': d.name}, 'name')
                if not job_card:
                    frappe.throw(_("Work Order {0}: Job Card not found for the operation {1}")
                                 .format(self.work_order, d.operation))

                work_order_link = frappe.utils.get_link_to_form('Work Order', self.work_order)
                job_card_link = frappe.utils.get_link_to_form('Job Card', job_card)
                # frappe.throw(_(
                #     "Row #{0}: Operation {1} is not completed for {2} qty of finished goods in Work Order {3}. Please update operation status via Job Card {4}.")
                #              .format(d.idx, frappe.bold(d.operation), frappe.bold(total_completed_qty),
                #                      work_order_link, job_card_link), OperationsNotCompleteError)


def produce_qty(doc, method):
    if doc.get('material_produce'):
        pro_doc = frappe.get_doc("Material Produce", doc.material_produce)
        pro_doc.produced = 1
        pro_doc.flags.ignore_validate_update_after_submit = True
        pro_doc.db_update()

def cancel_produce_qty(doc, method):
    if doc.get('material_produce'):
        pro_doc = frappe.get_doc("Material Produce", doc.material_produce)
        pro_doc.produced = 0
        pro_doc.flags.ignore_validate_update_after_submit = True
        pro_doc.db_update()

def change_work_order_status(doc, method):
    if doc.completed_work_order:
        wo = frappe.get_doc("Work Order",doc.work_order)
        wo.status = "Completed"
        wo.docstatus = 1
        wo.db_update()

def set_material_cost(doc,method):
    if doc.material_consumption:
        m_doc = frappe.get_doc("Material Consumption", doc.material_consumption)
        m_doc.cost_of_consumption = doc.total_outgoing_value
        m_doc.db_update()
        if doc.work_order:
            wo = frappe.get_doc("Work Order", doc.work_order)
            if wo.actual_rm_cost:
                wo.actual_rm_cost += doc.total_outgoing_value
            else:
                wo.actual_rm_cost += doc.total_outgoing_value
            wo.db_update()

    if doc.get('material_produce'):
        qty_produced = 0
        for res in doc.items:
            if res.is_finished_item:
                qty_produced += res.qty

        wo = frappe.get_doc("Work Order", doc.work_order)
        pro_doc = frappe.get_doc("Material Produce", doc.material_produce)
        if pro_doc.partial_produce:
            pro_doc.cost_of_rm_consumed = (wo.planned_rm_cost / wo.qty) * qty_produced
            pro_doc.cost_of_operation_consumed = doc.total_additional_costs
        pro_doc.db_update()