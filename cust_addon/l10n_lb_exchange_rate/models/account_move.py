from odoo import _, api, fields, models
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'currency.mixin']

    is_currency_locked_document = fields.Boolean(compute='_compute_currency_lock')
    has_recomputed = fields.Boolean()

    total_lbp = fields.Float(compute='_compute_totals_in_curr')
    total_gov = fields.Float(compute='_compute_totals_in_curr')
    total_untaxed_gov = fields.Float(compute='_compute_totals_in_curr')
    total_gov_tax = fields.Float(compute='_compute_totals_in_curr')

    @api.depends('invoice_date', 'currency_id', 'amount_total', 'special_currency_rate', 'use_special_rate')
    def _compute_totals_in_curr(self):
        for move in self:
            move.total_lbp = sum(move.line_ids.mapped('lbp_credit'))
            total_untaxed_gov = sum(move.invoice_line_ids.mapped('total_gov'))
            total_gov_tax = sum(move.line_ids.mapped('total_tax_amount'))
            move.total_gov = total_untaxed_gov + total_gov_tax
            move.total_untaxed_gov = total_untaxed_gov
            move.total_gov_tax = total_gov_tax

    def _get_amount_total_in_currency(self, amount, currency_id):
        return self._currency_context().currency_id._convert(
            amount,
            currency_id,
            self.company_id,
            self.invoice_date or fields.Date.context_today(self),
        )

    def _post(self, soft=True):
        for move in self.filtered(lambda r: r.country_code == 'LB'):
            if float_is_zero(move.special_currency_rate, precision_rounding=2):
                move.special_currency_rate = move.company_id.lbp_id.rate
            move.recompute_journal_items()
        return super()._post(soft)

    def recompute_journal_items(self):
        self.ensure_one()
        self._recompute_dynamic_lines()
        for line in self.line_ids:
            line.write(line._prepare_lebanon_data(line.credit, line.debit))  # force recompute values.
        self._compute_totals_in_curr()
        if not self.env.context.get('avoid_recursion'):
            self.with_context(avoid_recursion=True).recompute_journal_items()

    @api.depends('invoice_line_ids')
    def _compute_currency_lock(self):
        """ To be overwritten """
        for record in self:
            record.is_currency_locked_document = False

    @api.onchange('special_currency_rate', 'use_special_rate', 'date', 'currency_id')
    def _onchange_currency(self):
        super()._onchange_currency()

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        for move in self:
            if move.country_code == 'LB':
                super(AccountMove, move._currency_context())._recompute_dynamic_lines(recompute_all_taxes,
                                                                                      recompute_tax_base_amount)
            else:
                super()._recompute_dynamic_lines(recompute_all_taxes, recompute_tax_base_amount)
            move.fix_rounding_errors()

    def fix_rounding_errors(self):
        self.ensure_one()
        debit = sum(self.line_ids.mapped('debit'))
        credit = sum(self.line_ids.mapped('credit'))
        diff = abs(debit - credit)
        rounding = self.currency_id.rounding

        if not float_is_zero(diff, precision_rounding=rounding) and \
                float_compare(diff, self.currency_id.rounding_fix, precision_rounding=rounding) <= 0:
            if float_compare(debit, credit, precision_rounding=rounding) > 0:
                max_line = self.line_ids.sorted(lambda r: r.debit)[-1]
                max_line.debit += debit - credit
            else:
                max_line = self.line_ids.sorted(lambda r: r.credit)[-1]
                max_line.debit += credit - debit

    def _inverse_amount_total(self):
        for move in self:
            if move.country_code == 'LB':
                super(AccountMove, move._currency_context())._inverse_amount_total()
            else:
                super()._inverse_amount_total()

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            if move.country_code == 'LB':
                super(AccountMove, move._currency_context())._compute_payments_widget_to_reconcile_info()
            else:
                super()._compute_payments_widget_to_reconcile_info()

    def _move_autocomplete_invoice_lines_values(self):
        if self.country_code == 'LB':
            return super(AccountMove, self._currency_context())._move_autocomplete_invoice_lines_values()
        return super(AccountMove, self)._move_autocomplete_invoice_lines_values()

    def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
        lines_vals = []
        for move in self:
            if move.country_code == 'LB':
                lines_vals += super(AccountMove,
                                    move._currency_context())._stock_account_prepare_anglo_saxon_in_lines_vals()
            else:
                lines_vals += super()._stock_account_prepare_anglo_saxon_in_lines_vals()
        return lines_vals

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        return super(AccountMove, self._currency_context())._recompute_tax_lines(recompute_tax_base_amount,
                                                                                 tax_rep_lines_to_recompute)

    # std function with slight mod.
    def _recompute_payment_terms_lines(self):
        """ Compute the dynamic payment term lines of the journal entry."""
        self.ensure_one()
        self = self.with_company(self.company_id)
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_company(self.journal_id.company_id)

        def _get_payment_terms_computation_date(self):
            '''Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            '''Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    (
                        'internal_type',
                        '=',
                        'receivable' if self.move_type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable',
                    ),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            """Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            """
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(
                    total_balance, date_ref=date, currency=self.company_id.currency_id
                )
                if self.currency_id == self.company_id.currency_id:
                    # Single-currency.
                    return [(b[0], b[1], b[1]) for b in to_compute]
                # Multi-currencies.
                to_compute_currency = self.invoice_payment_term_id.compute(
                    total_amount_currency, date_ref=date, currency=self.currency_id
                )
                return [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute, currency_rate=False):
            """Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            """
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency in to_compute:
                currency = self.journal_id.company_id.currency_id
                if currency and currency.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    update_dict = {
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                    }
                    if currency_rate:  # custo code
                        update_dict['special_currency_rate'] = currency_rate
                    candidate.update(update_dict)
                else:
                    # Create new line.
                    create_method = (
                        in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                    )
                    create_dict = {
                        'name': self.payment_reference or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                    }
                    if currency_rate:
                        create_dict['special_currency_rate'] = currency_rate
                    candidate = create_method(create_dict)
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')
        )
        others_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable')
        )
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))
        if not others_lines:
            self.line_ids -= existing_terms_lines
            return
        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        currency_rate = (
            to_compute and to_compute[0][1] and abs(sum(others_lines.mapped('total_lbp')) / to_compute[0][1])
        )  # custo code
        new_terms_lines = _compute_diff_payment_terms_lines(
            self, existing_terms_lines, account, to_compute, currency_rate  # custo code
        )
        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.payment_reference = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line', 'currency.mixin']

    special_currency_rate = fields.Float(compute='compute_special_rate_aml', store=True)
    use_special_rate = fields.Boolean(related='move_id.use_special_rate', store=True)
    total_usl = fields.Float(readonly=True)
    total_lbp = fields.Float(readonly=True)
    total_gov = fields.Float(readonly=True)
    gov_balance = fields.Float(readonly=True)
    total_tax_amount = fields.Float(compute='_compute_total_tax_amount', store=True)
    lbp_credit = fields.Float(readonly=True)
    lbp_debit = fields.Float(readonly=True)
    gov_credit = fields.Float(readonly=True)
    gov_debit = fields.Float(readonly=True)
    is_tax_line = fields.Boolean(compute='_compute_is_tax_line', store=True)

    @api.depends('total_gov', 'company_id.gov_lbp_id', 'quantity', 'product_id', 'move_id.partner_id')
    def _compute_total_tax_amount(self):
        for line in self:
            if not line.exclude_from_invoice_tab and line.tax_ids:
                tax_amount = line.tax_ids.compute_all(abs(line.balance), currency=line.company_id.currency_id,
                                                      quantity=1, product=line.product_id,
                                                      partner=line.move_id.partner_id)

                if line.currency_id != line.company_id.country_currency_id:
                    currency_id = line.company_id.gov_lbp_id
                else:
                    currency_id = line.company_id.lbp_id
                total_included = line.get_lebanon_journal_item(tax_amount['total_included'], currency_id)
                total_excluded = line.get_lebanon_journal_item(tax_amount['total_excluded'], currency_id)
                line.total_tax_amount = total_included - total_excluded
            else:
                line.total_tax_amount = 0

    @api.depends('tax_line_id')
    def _compute_is_tax_line(self):
        tax_line_ids = self.filtered(lambda r: r.tax_line_id)
        tax_line_ids.update({'is_tax_line': True})
        (self - tax_line_ids).update({'is_tax_line': False})

    @api.depends('move_id.special_currency_rate', 'currency_id')
    def compute_special_rate_aml(self):
        for line in self:
            if line.is_tax_line and line.currency_id != self.env.company.country_currency_id:
                line.special_currency_rate = self.env.company.gov_lbp_id.rate
            else:
                line.special_currency_rate = line.move_id.special_currency_rate

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        for line in self:
            if line.move_id.country_code == 'LB':
                super(AccountMoveLine, line._currency_context())._onchange_price_subtotal()
            else:
                super(AccountMoveLine, line)._onchange_price_subtotal()

    @api.onchange('currency_id', 'special_currency_rate', 'use_special_rate')
    def _onchange_currency(self):
        if self.move_id.country_code == 'LB':
            return super(AccountMoveLine, self._currency_context())._onchange_currency()
        return super(AccountMoveLine, self)._onchange_currency()

    @api.onchange('tax_totals_json')
    def _onchange_tax_totals_json(self):
        if self.move_id.country_code == 'LB':
            return super(AccountMoveLine, self._currency_context())._onchange_tax_totals_json()
        return super(AccountMoveLine, self)._onchange_tax_totals_json()

    def _prepare_lebanon_data(self, credit, debit):
        self.ensure_one()
        lbp_id = self.company_id.lbp_id
        usl_id = self.company_id.usl_id
        gov_lbp_id = self.company_id.gov_lbp_id
        balance = debit or credit
        res = {
            'total_usl': self.get_lebanon_journal_item(balance, usl_id, absolute=True),
            'total_lbp': self.get_lebanon_journal_item(balance, lbp_id, absolute=True),
            'lbp_credit': self.get_lebanon_journal_item(credit, lbp_id),
            'lbp_debit': self.get_lebanon_journal_item(debit, lbp_id),
        }
        if self.currency_id != self.company_id.country_currency_id:
            currency_id = gov_lbp_id
        else:
            currency_id = lbp_id
        res.update({
            'total_gov': self.get_lebanon_journal_item(balance, currency_id, absolute=True),
            'gov_balance': self.get_lebanon_journal_item(debit - credit, currency_id),
            'gov_debit': self.get_lebanon_journal_item(debit, currency_id),
            'gov_credit': self.get_lebanon_journal_item(credit, currency_id),
        })
        return res

    def get_lebanon_journal_item(self, balance, currency_id, absolute=False):
        return self._currency_context().company_currency_id._convert(
            abs(balance) if absolute else balance,
            currency_id,
            self.company_id,
            self.date or fields.Date.context_today(self),
        )

    @api.model
    def _get_fields_onchange_subtotal_model(self, price_subtotal=None, move_type=None, currency=None, company=None,
                                            date=None):
        if self.move_id.country_code != 'LB':
            return super()._get_fields_onchange_subtotal_model(price_subtotal, move_type, currency, company, date)

        res = super(AccountMoveLine, self and self._currency_context())._get_fields_onchange_subtotal_model(
            price_subtotal, move_type, currency, company, date
        )
        res.update(self._prepare_lebanon_data(res['credit'], res['debit']))
        return res

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None,
                                      partner=None, taxes=None, move_type=None):
        if self.move_id.country_code != 'LB':
            return super()._get_price_total_and_subtotal(price_unit, quantity, discount, currency, product, partner,
                                                         taxes, move_type)
        return super(AccountMoveLine, self._currency_context())._get_price_total_and_subtotal(
            price_unit, quantity, discount, currency, product, partner, taxes, move_type)

    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        for line in self:
            if line.move_id.country_code == 'LB':
                super(AccountMoveLine, line._currency_context())._onchange_amount_currency()
            else:
                super()._onchange_amount_currency()

    # STD function
    def _prepare_reconciliation_partials(self):
        def fix_remaining_cent(currency, abs_residual, partial_amount):
            if abs_residual - currency.rounding <= partial_amount <= abs_residual + currency.rounding:
                return abs_residual
            else:
                return partial_amount

        debit_lines = iter(self.filtered(lambda line: line.balance > 0.0 or line.amount_currency > 0.0))
        credit_lines = iter(self.filtered(lambda line: line.balance < 0.0 or line.amount_currency < 0.0))
        debit_line = None
        credit_line = None

        debit_amount_residual = 0.0
        debit_amount_residual_currency = 0.0
        credit_amount_residual = 0.0
        credit_amount_residual_currency = 0.0
        debit_line_currency = None
        credit_line_currency = None

        partials_vals_list = []

        while True:
            if not debit_line:
                debit_line = next(debit_lines, None)
                if not debit_line:
                    break
                if debit_line.move_id.country_code == 'LB':
                    debit_line = debit_line._currency_context()  # custo code
                debit_amount_residual = debit_line.amount_residual

                if debit_line.currency_id:
                    debit_amount_residual_currency = debit_line.amount_residual_currency
                    debit_line_currency = debit_line.currency_id
                else:
                    debit_amount_residual_currency = debit_amount_residual
                    debit_line_currency = debit_line.company_currency_id
            if not credit_line:
                credit_line = next(credit_lines, None)
                if not credit_line:
                    break
                if credit_line.move_id.country_code == 'LB':
                    credit_line = credit_line._currency_context()  # custo code
                credit_amount_residual = credit_line.amount_residual

                if credit_line.currency_id:
                    credit_amount_residual_currency = credit_line.amount_residual_currency
                    credit_line_currency = credit_line.currency_id
                else:
                    credit_amount_residual_currency = credit_amount_residual
                    credit_line_currency = credit_line.company_currency_id
            min_amount_residual = min(debit_amount_residual, -credit_amount_residual)
            has_debit_residual_left = (
                not debit_line.company_currency_id.is_zero(debit_amount_residual) and debit_amount_residual > 0.0
            )
            has_credit_residual_left = (
                not credit_line.company_currency_id.is_zero(credit_amount_residual) and credit_amount_residual < 0.0
            )
            has_debit_residual_curr_left = (
                not debit_line_currency.is_zero(debit_amount_residual_currency) and debit_amount_residual_currency > 0.0
            )
            has_credit_residual_curr_left = (
                not credit_line_currency.is_zero(credit_amount_residual_currency)
                and credit_amount_residual_currency < 0.0
            )

            if debit_line_currency == credit_line_currency:
                if not has_debit_residual_curr_left and (has_credit_residual_curr_left or not has_debit_residual_left):
                    debit_line = None
                    continue
                if not has_credit_residual_curr_left and (has_debit_residual_curr_left or not has_credit_residual_left):
                    credit_line = None
                    continue

                min_amount_residual_currency = min(debit_amount_residual_currency, -credit_amount_residual_currency)
                min_debit_amount_residual_currency = min_amount_residual_currency
                min_credit_amount_residual_currency = min_amount_residual_currency

            else:
                if not has_debit_residual_left:
                    debit_line = None
                    continue
                if not has_credit_residual_left:
                    credit_line = None
                    continue
                min_debit_amount_residual_currency = credit_line.company_currency_id._convert(
                    min_amount_residual,
                    debit_line.currency_id,
                    credit_line.company_id,
                    credit_line.date,
                )
                min_debit_amount_residual_currency = fix_remaining_cent(
                    debit_line.currency_id,
                    debit_amount_residual_currency,
                    min_debit_amount_residual_currency,
                )
                min_credit_amount_residual_currency = debit_line.company_currency_id._convert(
                    min_amount_residual,
                    credit_line.currency_id,
                    debit_line.company_id,
                    debit_line.date,
                )
                min_credit_amount_residual_currency = fix_remaining_cent(
                    credit_line.currency_id,
                    -credit_amount_residual_currency,
                    min_credit_amount_residual_currency,
                )

            debit_amount_residual -= min_amount_residual
            debit_amount_residual_currency -= min_debit_amount_residual_currency
            credit_amount_residual += min_amount_residual
            credit_amount_residual_currency += min_credit_amount_residual_currency

            partials_vals_list.append(
                {
                    'amount': min_amount_residual,
                    'debit_amount_currency': min_debit_amount_residual_currency,
                    'credit_amount_currency': min_credit_amount_residual_currency,
                    'debit_move_id': debit_line.id,
                    'credit_move_id': credit_line.id,
                }
            )
        return partials_vals_list
