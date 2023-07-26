from odoo import api, models


class AccountGeneralLedger(models.AbstractModel):
    _inherit = "account.general.ledger"

    filter_secondary_currency = False

    def _get_lines(self, options, line_id=None):
        return super(
            AccountGeneralLedger, self.with_context(secondary_currency=options.get("secondary_currency"))
        )._get_lines(options, line_id=line_id)

    def _get_table(self, options):
        return super(
            AccountGeneralLedger, self.with_context(secondary_currency=options.get("secondary_currency"))
        )._get_table(options)

    @api.model
    def _get_query_sums(self, options_list, expanded_account=None):  # standard code with custo mod
        if not options_list[0].get("secondary_currency") or not self.env.company.report_currency_id:
            return super()._get_query_sums(options_list, expanded_account)
        options = options_list[0]
        unfold_all = options.get("unfold_all") or (self._context.get("print_mode") and not options["unfolded_lines"])

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = self.env["res.currency"]._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================

        domain = [("account_id", "=", expanded_account.id)] if expanded_account else []
        secondary_currency_precision = str(self.env.company.report_currency_id.decimal_places)
        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_to']),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True),
            # ]

            new_options = self._get_options_sum_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            # Custo start
            if self.env.company.gov_lbp_id == self.env.company.report_currency_id:
                aml = """
                    SUM(COALESCE(account_move_line.gov_debit, 0.0)) AS debit,
                    SUM(COALESCE(account_move_line.gov_credit, 0.0)) AS credit,
                    SUM(COALESCE(account_move_line.gov_balance, 0.0)) AS balance
                """
            else:
                aml = """
                    SUM(ROUND(account_move_line.debit * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s))   AS debit,
                    SUM(ROUND(account_move_line.credit * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s))  AS credit,
                    SUM(ROUND(account_move_line.balance * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s)) AS balance
                """ % (secondary_currency_precision, secondary_currency_precision, secondary_currency_precision)
            string = f"""
                SELECT
                    account_move_line.account_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    {i}                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    {aml}
                FROM {tables}
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN (SELECT a.id ,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = {self.env.company.report_currency_id.id} AND r.name <= a.date
                                    AND (r.company_id IS NULL OR r.company_id = {self.env.company.id})
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) as rate
                   FROM account_move_line as a) c2
                on c2.id = account_move_line.id
                WHERE {where_clause}
                GROUP BY account_move_line.account_id
            """
            # custo end
            queries.append(string)

        # ============================================
        # 2) Get sums for the unaffected earnings.
        # ============================================

        domain = [("account_id.user_type_id.include_initial_balance", "=", False)]
        if expanded_account:
            domain.append(("company_id", "=", expanded_account.company_id.id))

        # Compute only the unaffected earnings for the oldest period.

        i = len(options_list) - 1
        options_period = options_list[-1]

        # The period domain is expressed as:
        # [
        #   ('date' <= fiscalyear['date_from'] - 1),
        #   ('account_id.user_type_id.include_initial_balance', '=', False),
        # ]

        new_options = self._get_options_unaffected_earnings(options_period)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        # custo start
        string = f"""
            SELECT
                account_move_line.company_id                            AS groupby,
                'unaffected_earnings'                                   AS key,
                NULL                                                    AS max_date,
                {i}                                                      AS period_number,
                COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                {aml}
            FROM {tables}
            LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN (SELECT a.id ,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = {self.env.company.report_currency_id.id}  AND r.name <= a.date
                                    AND (r.company_id IS NULL OR r.company_id = {self.env.company.id})
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) as rate
                   FROM account_move_line as a) c2
                on c2.id = account_move_line.id
            WHERE {where_clause}
            GROUP BY account_move_line.company_id
        """
        # custo end
        queries.append(string)

        # ============================================
        # 3) Get sums for the initial balance.
        # ============================================

        domain = []
        if expanded_account:
            domain = [("account_id", "=", expanded_account.id)]
        elif not unfold_all and options["unfolded_lines"]:
            domain = [("account_id", "in", [int(line[8:]) for line in options["unfolded_lines"]])]

        for i, options_period in enumerate(options_list):

            # The period domain is expressed as:
            # [
            #   ('date' <= options['date_from'] - 1),
            #   '|',
            #   ('date' >= fiscalyear['date_from']),
            #   ('account_id.user_type_id.include_initial_balance', '=', True)
            # ]

            new_options = self._get_options_initial_balance(options_period)
            tables, where_clause, where_params = self._query_get(new_options, domain=domain)
            params += where_params
            # custo start
            string = f"""
                SELECT
                    account_move_line.account_id                            AS groupby,
                    'initial_balance'                                       AS key,
                    NULL                                                    AS max_date,
                    {i}                                                      AS period_number,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    {aml}
                FROM {tables}
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN (SELECT a.id ,
                      COALESCE((SELECT r.rate FROM res_currency_rate r
                              WHERE r.currency_id = {self.env.company.report_currency_id.id}  AND r.name <= a.date
                                AND (r.company_id IS NULL OR r.company_id = {self.env.company.id})
                           ORDER BY r.company_id, r.name DESC
                              LIMIT 1), 1.0) as rate
                FROM account_move_line as a) c2
                on c2.id = account_move_line.id
                WHERE {where_clause}
                GROUP BY account_move_line.account_id
            """
            # custo end
            queries.append(string)

        # ============================================
        # 4) Get sums for the tax declaration.
        # ============================================

        journal_options = self._get_options_journals(options)
        if not expanded_account and len(journal_options) == 1 and journal_options[0]["type"] in ("sale", "purchase"):
            for i, options_period in enumerate(options_list):
                tables, where_clause, where_params = self._query_get(options_period)
                params += where_params + where_params
                # custo start
                if self.env.company.gov_lbp_id == self.env.company.report_currency_id:
                    balance_select = """
                        SUM(COALESCE(account_move_line.gov_balance, 0.0)) AS balance
                    """
                else:
                    balance_select = """
                        SUM(ROUND(account_move_line.balance * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s)) AS balance
                    """ % (secondary_currency_precision,)
                string_1 = f"""
                    SELECT
                        tax_rel.account_tax_id                  AS groupby,
                        'base_amount'                           AS key,
                        NULL                                    AS max_date,
                        {i}                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        {balance_select}
                    FROM account_move_line_account_tax_rel tax_rel, {tables}
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    LEFT JOIN (SELECT a.id ,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = {self.env.company.report_currency_id.id} AND r.name <= a.date
                                    AND (r.company_id IS NULL OR r.company_id = {self.env.company.id})
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) as rate
                    FROM account_move_line as a) c2
                    on c2.id = account_move_line.id
                    WHERE account_move_line.id = tax_rel.account_move_line_id AND {where_clause}
                    GROUP BY tax_rel.account_tax_id
                """
                string_2 = f"""
                    SELECT
                    account_move_line.tax_line_id               AS groupby,
                    'tax_amount'                                AS key,
                        NULL                                    AS max_date,
                        {i}                                      AS period_number,
                        0.0                                     AS amount_currency,
                        0.0                                     AS debit,
                        0.0                                     AS credit,
                        {balance_select}
                    FROM {tables}
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    LEFT JOIN (SELECT a.id ,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = {self.env.company.report_currency_id.id}  AND r.name <= a.date
                                    AND (r.company_id IS NULL OR r.company_id = {self.env.company.id})
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) as rate
                    FROM account_move_line as a) c2
                    on c2.id = account_move_line.id
                    WHERE {where_clause}
                    GROUP BY account_move_line.tax_line_id
                """
                # custo end
                queries += [string_1, string_2]

        return " UNION ALL ".join(queries), params

    # Odoo standard function with customization
    @api.model
    def _get_query_amls(self, options, expanded_account, offset=None, limit=None):
        if not options.get("secondary_currency") or not self.env.company.report_currency_id:
            return super()._get_query_amls(options, expanded_account, offset, limit)

        unfold_all = options.get("unfold_all") or (self._context.get("print_mode") and not options["unfolded_lines"])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_account:
            domain = [("account_id", "=", expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options["unfolded_lines"]:
            domain = [("account_id", "in", [int(line[8:]) for line in options["unfolded_lines"]])]

        new_options = self._force_strict_range(options)
        secondary_currency_precision = str(self.env.company.report_currency_id.decimal_places)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self.env["res.currency"]._get_query_currency_table(options)
        # custo start
        select = """
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                account_move_line.name,
                account_move_line.ref,
                account_move_line.company_id,
                account_move_line.account_id,
                account_move_line.payment_id,
                account_move_line.partner_id,
                account_move_line.currency_id,
                account_move_line.amount_currency,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                account_move_line__move_id.move_type         AS move_type,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name,
                full_rec.name                           AS full_rec_name,
        """
        if self.env.company.gov_lbp_id == self.env.company.report_currency_id:
            select += """
                COALESCE(account_move_line.gov_debit, 0.0) AS debit,
                COALESCE(account_move_line.gov_credit, 0.0) AS credit,
                COALESCE(account_move_line.gov_balance, 0.0) AS balance
            """
        else:
            select += """
                ROUND(account_move_line.debit  * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s)   AS debit,
                ROUND(account_move_line.credit  * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s)  AS credit,
                ROUND(account_move_line.balance  * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s) AS balance
                
            """ % (secondary_currency_precision, secondary_currency_precision, secondary_currency_precision)
        query = f"""
            
            FROM account_move_line
            LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
            LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
            LEFT JOIN (SELECT a.id ,
                    COALESCE((SELECT r.rate FROM res_currency_rate r
                            WHERE r.currency_id = {self.env.company.report_currency_id.id}  AND r.name <= a.date
                              AND (r.company_id IS NULL OR r.company_id = {self.env.company.id})
                         ORDER BY r.company_id, r.name DESC
                            LIMIT 1), 1.0) as rate
            FROM account_move_line as a) c2 ON c2.id = account_move_line.id
            WHERE {where_clause}
            ORDER BY account_move_line.date, account_move_line.id
        """
        # custo end
        if offset:
            query += " OFFSET %s "
            where_params.append(offset)
        if limit:
            query += " LIMIT %s "
            where_params.append(limit)

        query = select + query

        return query, where_params
