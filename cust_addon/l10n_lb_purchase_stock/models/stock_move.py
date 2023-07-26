from odoo import api, fields, models
from odoo.tools import OrderedSet, float_compare, float_is_zero, float_round


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env["decimal.precision"].precision_get("Product Price")
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = line.taxes_id.with_context(round=False).compute_all(
                    price_unit, currency=line.order_id.currency_id, quantity=qty
                )["total_void"]
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.with_context(
                    use_special_rate=order.use_special_rate,
                    special_currency_rate=order.use_special_rate and order.special_currency_rate,
                ).currency_id._convert(
                    price_unit,
                    order.company_id.currency_id,
                    order.company_id,
                    fields.Date.context_today(self),
                    round=False,
                )
            return price_unit
        return super(StockMove, self)._get_price_unit()
