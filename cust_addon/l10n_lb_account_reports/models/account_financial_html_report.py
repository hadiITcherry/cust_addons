from odoo import api, models


class AccountReport(models.AbstractModel):
    _inherit = "account.report"
    _description = "Account Report"

    @api.model
    def format_value(self, amount, currency=False, blank_if_zero=False):
        if not currency and self.env.context.get("secondary_currency"):
            currency = self.env.company.report_currency_id
        return super().format_value(amount, currency=currency, blank_if_zero=blank_if_zero)


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"
    filter_secondary_currency = False

    def _get_lines(self, options, line_id=None):
        self.ensure_one()
        return super(
            ReportAccountFinancialReport, self.with_context(secondary_currency=options.get("secondary_currency"))
        )._get_lines(options, line_id=line_id)

    def _get_table(self, options):
        self.ensure_one()
        return super(
            ReportAccountFinancialReport, self.with_context(secondary_currency=options.get("secondary_currency"))
        )._get_table(options)


class AccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report.line"

    def _compute_amls_results(self, options_list, calling_financial_report=None, sign=1, operator=None):
        show_secondary_currency = options_list[0].get("secondary_currency")
        secondary_currency_precision = str(self.env.company.report_currency_id.decimal_places)
        if (not show_secondary_currency) or not self.env.company.report_currency_id:
            return super()._compute_amls_results(options_list, calling_financial_report, sign, operator)
        self.ensure_one()
        AccountFinancialReportHtml = self.financial_report_id
        params = []
        queries = []
        horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_list = [self.groupby] + horizontal_groupby_list
        groupby_clause = ",".join("account_move_line.%s" % gb for gb in groupby_list)
        groupby_field = self.env["account.move.line"]._fields[self.groupby]

        ct_query = self.env["res.currency"]._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)
            # custom code starts
            if self.env.company.gov_lbp_id == self.env.company.report_currency_id:
                balance_select = """
                    COALESCE(SUM(COALESCE(account_move_line.gov_balance, 0.0)), 0.0) AS balance
                """
            else:
                balance_select = """
                    COALESCE(SUM(ROUND(account_move_line.balance * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s)), 0.0) AS balance
                """ % (secondary_currency_precision,)
            queries.append(
                """
                SELECT
                    """
                + (groupby_clause and "%s," % groupby_clause)
                + """
                    %s AS period_index,
                    """
                + balance_select +
                """
                FROM """
                + tables
                + """
                JOIN """
                + ct_query
                + """ ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN (SELECT a.id ,
                    COALESCE((SELECT r.rate FROM res_currency_rate r
                        WHERE r.currency_id = """
                + str(self.env.company.report_currency_id.id)
                + """  AND r.name <= a.date
                            AND (r.company_id IS NULL OR r.company_id = """
                + str(self.env.company.id)
                + """)
                            ORDER BY r.company_id, r.name DESC
                            LIMIT 1), 1.0) as rate
                    FROM account_move_line as a) c2
                    on c2.id = account_move_line.id
                WHERE """
                + where_clause
                + """
                """
                + (groupby_clause and "GROUP BY %s" % groupby_clause)
                + """
            """
            )
            params += [i] + where_params
        # custom code ends
        # Fetch the results.
        # /!\ Take care of both vertical and horizontal group by clauses.

        results = {}
        total_balance = 0.0
        self._cr.execute(" UNION ALL ".join(queries), params)
        for res in self._cr.dictfetchall():
            balance = res["balance"]
            total_balance += balance

            # Build the key.
            key = [res["period_index"]]
            for gb in horizontal_groupby_list:
                key.append(res[gb])
            key = tuple(key)

            add_line = (
                not operator
                or operator in ("sum", "sum_if_pos", "sum_if_neg")
                or (operator == "sum_if_pos_groupby" and balance >= 0.0)
                or (operator == "sum_if_neg_groupby" and balance < 0.0)
            )

            if add_line:
                results.setdefault(res[self.groupby], {})
                results[res[self.groupby]][key] = sign * balance

        add_line = (
            not operator
            or operator in ("sum", "sum_if_pos_groupby", "sum_if_neg_groupby")
            or (operator == "sum_if_pos" and total_balance >= 0.0)
            or (operator == "sum_if_neg" and total_balance < 0.0)
        )
        if not add_line:
            results = {}

        # Sort the lines according to the vertical groupby and compute their display name.
        if groupby_field.relational:
            # Preserve the table order by using search instead of browse.
            sorted_records = self.env[groupby_field.comodel_name].search([("id", "in", tuple(results.keys()))])
            sorted_values = sorted_records.name_get()
        else:
            # Sort the keys in a lexicographic order.
            sorted_values = [(v, v) for v in sorted(list(results.keys()))]

        return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]

    def _compute_sum(self, options_list, calling_financial_report=None):
        self.ensure_one()
        show_secondary_currency = options_list[0].get("secondary_currency")
        secondary_currency_precision = str(self.env.company.report_currency_id.decimal_places)
        AccountFinancialReportHtml = self.financial_report_id
        if (not show_secondary_currency) or not self.env.company.report_currency_id:
            return super()._compute_sum(options_list, calling_financial_report)
        params = []
        queries = []
        groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        all_groupby_list = groupby_list.copy()
        groupby_in_formula = any(x in (self.formulas or "") for x in ("sum_if_pos_groupby", "sum_if_neg_groupby"))
        if groupby_in_formula and self.groupby and self.groupby not in all_groupby_list:
            all_groupby_list.append(self.groupby)
        groupby_clause = ",".join("account_move_line.%s" % gb for gb in all_groupby_list)

        ct_query = self.env["res.currency"]._get_query_currency_table(options_list[0])
        parent_financial_report = self._get_financial_report()

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options, calling_financial_report, parent_financial_report)
            line_domain = self._get_domain(new_options, parent_financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)
            # custom code starts
            if self.env.company.gov_lbp_id == self.env.company.report_currency_id:
                balance_select = """
                    COALESCE(SUM(COALESCE(account_move_line.gov_balance, 0.0)), 0.0) AS balance
                """
            else:
                balance_select = """
                    COALESCE(SUM(ROUND(account_move_line.balance * CAST(COALESCE(NULLIF(account_move_line.special_currency_rate, 0.0), c2.rate/currency_table.rate) AS numeric), %s)), 0.0) AS balance
                """ % (secondary_currency_precision,)
            queries.append(
                """
                SELECT
                    """
                + (groupby_clause and "%s," % groupby_clause)
                + """ %s AS period_index,
                    COUNT(DISTINCT account_move_line."""
                + (self.groupby or "id")
                + """) AS count_rows,"""
                + balance_select +
                """
                FROM """
                + tables
                + """
                JOIN """
                + ct_query
                + """ ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN (SELECT a.id ,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = """
                + str(self.env.company.report_currency_id.id)
                + """  AND r.name <= a.date
                                    AND (r.company_id IS NULL OR r.company_id = """
                + str(self.env.company.id)
                + """)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) as rate
                    FROM account_move_line as a) c2
                    on c2.id = account_move_line.id
                WHERE """
                + where_clause
                + """
                """
                + (groupby_clause and "GROUP BY %s" % groupby_clause)
                + """
            """
            )
            params.append(i)
            params += where_params
        # custom code ends
        # Fetch the results.

        results = {
            "sum": {},
            "sum_if_pos": {},
            "sum_if_pos_groupby": {},
            "sum_if_neg": {},
            "sum_if_neg_groupby": {},
            "count_rows": {},
        }

        self._cr.execute(" UNION ALL ".join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res["period_index"]]
            for gb in groupby_list:
                key.append(res[gb])
            key = tuple(key)

            # Compute values.
            results["count_rows"].setdefault(res["period_index"], 0)
            results["count_rows"][res["period_index"]] += res["count_rows"]
            results["sum"][key] = res["balance"]
            if results["sum"][key] > 0:
                results["sum_if_pos"][key] = results["sum"][key]
                results["sum_if_pos_groupby"].setdefault(key, 0.0)
                results["sum_if_pos_groupby"][key] += res["balance"]
            if results["sum"][key] < 0:
                results["sum_if_neg"][key] = results["sum"][key]
                results["sum_if_neg_groupby"].setdefault(key, 0.0)
                results["sum_if_neg_groupby"][key] += res["balance"]

        return results
