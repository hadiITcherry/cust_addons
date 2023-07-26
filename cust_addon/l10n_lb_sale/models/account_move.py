from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one("sale.order", related="invoice_line_ids.sale_line_ids.order_id", store=True)

    def _compute_currency_lock(self):
        super()._compute_currency_lock()
        for record in self:
            record.is_currency_locked_document = bool(record.is_currency_locked_document or record.sale_order_id)
