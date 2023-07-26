from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "currency.mixin"]

    account_move_currency_id = fields.Many2one("res.currency", "Bill Currency")
    total_usl = fields.Float(string="Total in bank rate", compute="_compute_multicurrency_amounts")
    total_lbp = fields.Float(string="Total in lbp_id", compute="_compute_multicurrency_amounts")
    total_tax = fields.Float(string="Tax Total lbp_id (USD Payment)", compute="_compute_multicurrency_amounts")
    country_code = fields.Char(related='company_id.account_fiscal_country_id.code')

    def button_confirm(self):
        for order in self:
            if float_is_zero(order.special_currency_rate, precision_rounding=2):
                order.special_currency_rate = order.company_id.lbp_id.rate
        return super().button_confirm()

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.account_move_currency_id.id:
            vals["currency_id"] = self.account_move_currency_id.id
        vals["special_currency_rate"] = self.special_currency_rate
        vals["use_special_rate"] = self.use_special_rate
        return vals

    @api.depends("date_order", "currency_id", "amount_total")
    def _compute_multicurrency_amounts(self):
        for record in self:
            lbp_id = record.company_id.lbp_id
            usl_id = record.company_id.usl_id
            record.total_usl = record._currency_context().currency_id._convert(
                record.amount_untaxed,
                usl_id,
                record.company_id,
                record.date_order or fields.Date.context_today(self),
            )
            record.total_lbp = record._currency_context().currency_id._convert(
                record.amount_untaxed,
                lbp_id,
                record.company_id,
                record.date_order or fields.Date.context_today(self),
            )
            record._compute_currency_rate()
            record._amount_all()
            record.total_tax = sum(record.order_line.mapped("total_tax"))


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "currency.mixin"]

    total_usl = fields.Float(string="Total in bank rate", compute="_compute_multicurrency_amounts")
    total_lbp = fields.Float(string="Total in lbp_id", compute="_compute_multicurrency_amounts")
    total_tax = fields.Float(string="Tax Total lbp_id (USD Payment)", compute="_compute_multicurrency_amounts")
    special_currency_rate = fields.Float(related="order_id.special_currency_rate", store=True)
    use_special_rate = fields.Boolean(related="order_id.use_special_rate", store=True)

    def _prepare_account_move_line(self, move=False):
        vals = super()._prepare_account_move_line(move)
        if self.order_id.account_move_currency_id.id:
            vals["price_unit"] = self._currency_context().currency_id._convert(
                self.price_unit,
                self.order_id.account_move_currency_id,
                self.order_id.company_id,
                self.order_id.date_order or fields.Date.today(),
            )
        return vals

    @api.depends("order_id.date_order", "currency_id", "price_total", "special_currency_rate", "use_special_rate")
    def _compute_multicurrency_amounts(self):
        for record in self:
            lbp_id = record.company_id.lbp_id
            usl_id = record.company_id.usl_id
            gov_lbp_id = record.company_id.gov_lbp_id
            record.total_usl = record._currency_context().currency_id._convert(
                record.price_subtotal,
                usl_id,
                record.company_id,
                record.order_id.date_order or fields.Date.today(),
            )
            record.total_lbp = record._currency_context().currency_id._convert(
                record.price_subtotal,
                lbp_id,
                record.company_id,
                record.order_id.date_order or fields.Date.today(),
            )
            record.total_tax = record._currency_context().currency_id._convert(
                record.price_tax,
                gov_lbp_id,
                record.company_id,
                record.order_id.date_order or fields.Date.today(),
            )
