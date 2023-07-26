from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    use_special_rate = fields.Boolean()
    special_currency_rate = fields.Float(string="lbp_id per USD")

    @api.model
    def _get_wizard_values_from_batch(self, batch_result):
        res = super()._get_wizard_values_from_batch(batch_result)
        payment_values = batch_result["payment_values"]
        line = batch_result["lines"][0]
        res.update(
            {
                "use_special_rate": line.use_special_rate,
                "special_currency_rate": line.special_currency_rate,
            }
        )
        return res

    def _compute_amount(self):
        super(
            AccountPaymentRegister,
            self.with_context(
                use_special_rate=self.use_special_rate,
                special_currency_rate=self.use_special_rate and self.special_currency_rate,
            ),
        )._compute_amount()

    def _compute_payment_difference(self):
        super(
            AccountPaymentRegister,
            self.with_context(
                use_special_rate=self.use_special_rate,
                special_currency_rate=self.use_special_rate and self.special_currency_rate,
            ),
        )._compute_payment_difference()

    def _create_payment_vals_from_wizard(self):
        res = super()._create_payment_vals_from_wizard()
        res.update({"use_special_rate": self.use_special_rate, "special_currency_rate": self.special_currency_rate})
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        res = super()._create_payment_vals_from_batch(batch_result)
        res.update({"use_special_rate": self.use_special_rate, "special_currency_rate": self.special_currency_rate})
        return res
