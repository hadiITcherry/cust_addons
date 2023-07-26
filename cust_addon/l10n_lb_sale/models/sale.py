from odoo import api, fields, models
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "currency.mixin"]

    account_move_currency_id = fields.Many2one("res.currency", "Invoice Currency")
    total_usl = fields.Float(string="Total bank", compute="_compute_multicurrency_amounts")
    total_lbp = fields.Float(string="Total LBP", compute="_compute_multicurrency_amounts")
    total_gov = fields.Float(string="Total gov", compute="_compute_multicurrency_amounts")
    total_untaxed_gov = fields.Float(string="Untaxed total in gov", compute="_compute_multicurrency_amounts")
    total_tax = fields.Float(string="Tax Total in gov", compute="_compute_multicurrency_amounts")
    country_code = fields.Char(related='company_id.account_fiscal_country_id.code')

    def action_confirm(self):
        for order in self:
            if float_is_zero(order.special_currency_rate, precision_rounding=2):
                order.special_currency_rate = order.company_id.lbp_id.rate
        return super().action_confirm()

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.account_move_currency_id.id:
            vals["currency_id"] = self.account_move_currency_id.id
        vals["special_currency_rate"] = self.special_currency_rate
        vals["use_special_rate"] = self.use_special_rate
        return vals

    @api.depends("date_order", "currency_id", "amount_total", "special_currency_rate", "use_special_rate")
    def _compute_multicurrency_amounts(self):
        for sale in self:
            sale.total_usl = sale._compute_amount_total_in_cur(sale.amount_total, sale.company_id.usl_id)
            sale.total_lbp = sale._compute_amount_total_in_cur(sale.amount_total, sale.company_id.lbp_id)
            total_untaxed_gov = sum(sale.order_line.mapped('total_gov'))
            total_tax = sum(sale.order_line.mapped('total_tax'))
            sale.total_gov = total_untaxed_gov + total_tax
            sale.total_untaxed_gov = total_untaxed_gov
            sale.total_tax = total_tax

    def _compute_amount_total_in_cur(self, amount, currency_id):
        return self._currency_context().currency_id._convert(
            amount,
            currency_id,
            self.company_id,
            self.date_order or fields.Date.context_today(self),)


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "currency.mixin"]

    total_usl = fields.Float(string="Total bank", compute="_compute_multicurrency_amounts")
    total_lbp = fields.Float(string="Total LPB", compute="_compute_multicurrency_amounts")
    total_gov = fields.Float(string="Total gov", compute="_compute_multicurrency_amounts")
    total_tax = fields.Float(string="Tax Total gov", compute="_compute_multicurrency_amounts")
    special_currency_rate = fields.Float(related="order_id.special_currency_rate", store=True)
    use_special_rate = fields.Boolean(related="order_id.use_special_rate", store=True)

    @api.onchange("product_id")
    def product_id_change(self):
        super(
            SaleOrderLine,
            self.with_context(
                use_special_rate=self.use_special_rate, special_currency_rate=self.order_id.special_currency_rate
            ),
        ).product_id_change()

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)
        if self.order_id.account_move_currency_id.id:
            vals["price_unit"] = self.with_context(
                use_special_rate=self.use_special_rate, special_currency_rate=self.special_currency_rate
            ).currency_id._convert(
                self.price_unit,
                self.order_id.account_move_currency_id,
                self.order_id.company_id,
                fields.Date.today(),
            )
        return vals

    @api.depends("order_id.date_order", "currency_id", "price_subtotal", "special_currency_rate", "use_special_rate")
    def _compute_multicurrency_amounts(self):
        for record in self:
            record.total_usl = record._compute_amount_in_cur(record.price_subtotal, record.company_id.usl_id)
            record.total_lbp = record._compute_amount_in_cur(record.price_subtotal, record.company_id.lbp_id)
            if record.order_id.account_move_currency_id == record.company_id.country_currency_id:
                currency_id = record.company_id.country_currency_id
            else:
                currency_id = record.company_id.gov_lbp_id
            record.total_gov = record._compute_amount_in_cur(record.price_subtotal, currency_id)
            record.total_tax = record._compute_amount_in_cur(record.price_tax, currency_id)

    def _compute_amount_in_cur(self, amount, currency_id):
        return self._currency_context().company_id.currency_id._convert(
                amount,
                currency_id,
                self.company_id,
                self.order_id.date_order or fields.Date.today(),
            )
