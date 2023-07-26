from odoo import api, fields, models, _
from odoo.tools.sql import column_exists, create_column
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _auto_init(self):
        # Since we are using these fields for defaults, defaults will run before the field is in
        if not column_exists(self.env.cr, 'res_company', 'gov_lbp_id'):
            create_column(self.env.cr, 'res_company', 'gov_lbp_id', 'int4')
            create_column(self.env.cr, 'res_company', 'lbp_id', 'int4')
            create_column(self.env.cr, 'res_company', 'usl_id', 'int4')
        return super()._auto_init()

    gov_lbp_id = fields.Many2one('res.currency', string='lebanese (Goverment) Currency')
    lbp_id = fields.Many2one('res.currency', string='lebanese (black market) Currency')
    usl_id = fields.Many2one('res.currency', string='Bank currency')
    country_currency_id = fields.Many2one('res.currency', related='country_id.currency_id', string='Country Currency')

    @api.constrains('gov_lbp_id', 'lbp_id', 'usl_id')
    def _constrains_lebanese_currencies(self):
        fields = ['gov_lbp_id', 'lbp_id', 'usl_id']
        data = self.read(fields)
        for rec in data:
            for field in fields:
                if rec[field]:  # dont compare empty fields
                    for field2 in fields:
                        if field != field2 and rec[field] == rec[field2]:
                            raise ValidationError(_('You cannot use the same currency for %s and %s') % (field, field2))
