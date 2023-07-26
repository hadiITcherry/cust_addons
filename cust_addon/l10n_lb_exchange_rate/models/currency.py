from odoo import api, fields, models


class Currency(models.Model):
    _inherit = "res.currency"

    rounding_fix = fields.Float(default=0.01)

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        # for safety
        # LPB TO GOV
        if to_currency == company.gov_lbp_id and from_currency == company.country_currency_id:
            return 1.0
        # GOV TO LBP
        if from_currency == company.gov_lbp_id and to_currency == company.country_currency_id:
            return 1.0
        # USD TO USD
        if from_currency == to_currency == company.currency_id or not self._context.get("use_special_rate"):
            return super(Currency, self)._get_conversion_rate(from_currency, to_currency, company, date)

        # USD TO LBP
        if from_currency == company.currency_id and to_currency == company.country_currency_id:
            return self._context.get("special_currency_rate") or 1
        # LBP TO USD
        if to_currency == company.currency_id and from_currency == company.country_currency_id:
            return 1 / (self._context.get("special_currency_rate") or 1)
        # FOREIGN TO LBP
        if to_currency == company.country_currency_id and from_currency != company.country_currency_id:
            # convert rate to usd
            return super()._get_conversion_rate(from_currency, company.currency_id, company, date) * self._context.get(
                "special_currency_rate"
            )
        # LBP TO FOREIGN
        if to_currency != company.country_currency_id and from_currency == company.country_currency_id:
            # convert rate to usd
            return super()._get_conversion_rate(company.currency_id, to_currency, company, date) / self._context.get(
                "special_currency_rate"
            )
        return super(Currency, self)._get_conversion_rate(from_currency, to_currency, company, date)
