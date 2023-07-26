from odoo import api, fields, models


class CurrencyMixin(models.AbstractModel):
    _name = "currency.mixin"
    _description = 'Special currency rate for Lebanon'

    def default_lbp_rate(self):
        return self.env.company.lbp_id.rate

    def default_lbc_rate(self):
        return self.env.company.usl_id.rate

    special_currency_rate = fields.Float(string="LBP per USD")
    latest_special_rate = fields.Float(default=default_lbp_rate, string='Backend LBP per USD')
    use_special_rate = fields.Boolean(compute='_compute_use_special_rate', store=True)
    latest_lbc_rate = fields.Float(default=default_lbc_rate, string="LBC per USD")

    @api.depends('country_code')
    def _compute_use_special_rate(self):
        for rec in self:
            rec.use_special_rate = rec.country_code == 'LB'

    def _currency_context(self):
        self.ensure_one()
        if not self._context.get("use_special_rate") or not self._context.get("special_currency_rate"):
            return self.with_context(
                use_special_rate=self.use_special_rate, special_currency_rate=self.special_currency_rate or self.default_lbp_rate()
            )
        return self
