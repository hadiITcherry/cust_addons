from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    report_currency_id = fields.Many2one("res.currency")
