# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FSMTag(models.Model):
    _name = "fsm.tag"
    _description = "Field Service Tag"

    name = fields.Char(required=True)
    color = fields.Integer("Color Index", default=10)
    description = fields.Char ("Description")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id,
        help="Company related to this tag",
    )
    _sql_constraints = [("name_uniq", "unique (name)", "Tag name already exists!")]
    icon = fields.Image(attachment=False,string="Icon")
    have_service_type = fields.Boolean(default = False,string="Have Service Types")
    priority = fields.Integer("Priority")
    # def _compute_full_name(self):
    #     for record in self:
    #         record.full_name = (
    #             record.parent_id.name + "/" + record.name
    #             if record.parent_id
    #             else record.name
    #         )
