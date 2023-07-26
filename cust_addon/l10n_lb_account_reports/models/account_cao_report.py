from odoo import api, models


class AccountCoaReport(models.AbstractModel):
    _inherit = "account.coa.report"

    filter_secondary_currency = False

    @api.model
    def _get_lines(self, options, line_id=None):
        return super(
            AccountCoaReport, self.with_context(secondary_currency=options.get("secondary_currency"))
        )._get_lines(options, line_id)
