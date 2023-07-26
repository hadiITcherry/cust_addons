from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    purchase_order_id = fields.Many2one("purchase.order", related="invoice_line_ids.purchase_line_id.order_id",
                                        store=True)

    def _compute_currency_lock(self):
        super()._compute_currency_lock()
        for record in self:
            record.is_currency_locked_document = bool(record.is_currency_locked_document or record.purchase_order_id)
