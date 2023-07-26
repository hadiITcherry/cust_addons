from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment", "currency.mixin"]

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        if self.country_code == 'LB':
            return super(AccountPayment, self._currency_context())._prepare_move_line_default_vals(write_off_line_vals)
        return super(AccountPayment, self)._prepare_move_line_default_vals()
