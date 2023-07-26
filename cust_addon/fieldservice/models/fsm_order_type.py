# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FSMOrderType(models.Model):
    _name = "fsm.order.type"
    _description = "Field Service Order Type"

    name = fields.Char(required=True,string="Type")

    internal_type = fields.Selection(
        selection=[("fsm", "FSM")],
        default="fsm",
    )

    service_id = fields.Many2one('fsm.tag','Service')
    image = fields.Image('icon',attachment=False)
    parent_id = fields.Many2one('fsm.order.type',"Parent")
    have_sub = fields.Boolean("Have Sub-Service?")
    priority = fields.Integer(string="Priority")
