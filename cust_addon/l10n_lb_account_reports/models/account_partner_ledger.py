# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import _, api, models


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    @api.model
    def _get_query_sums(self, options, expanded_partner=None):
        """Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all partners.
        - sums for the initial balances.
        :param options:             The report options.
        :param expanded_partner:    An optional res.partner record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        """
        params = []
        queries = []
        domain = []
        if expanded_partner is not None:
            domain = [("partner_id", "=", expanded_partner.id)]

        # Create the currency table.
        ct_query = self.env["res.currency"]._get_query_currency_table(options)

        new_options = self._get_options_sum_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        # custo start
        queries.append(
            """
            SELECT
                account_move_line.partner_id        AS groupby,
                'sum'                               AS key,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.amount_currency) AS amount_currency,
                MAX(account_move_line.currency_id) AS currency_id,
                count(distinct account_move_line.currency_id) AS distinct_currencies
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.partner_id
        """
            % (tables, ct_query, where_clause)
        )
        # custo
        new_options = self._get_options_initial_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        # custo code starts
        queries.append(
            """
            SELECT
                account_move_line.partner_id        AS groupby,
                'initial_balance'                   AS key,
                SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                SUM(account_move_line.amount_currency) AS amount_currency,
                MAX(account_move_line.currency_id) AS currency_id,
                count(distinct account_move_line.currency_id) AS distinct_currencies
            FROM %s
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            WHERE %s
            GROUP BY account_move_line.partner_id
        """
            % (tables, ct_query, where_clause)
        )
        # custo code ends
        return " UNION ALL ".join(queries), params

    @api.model
    def _get_sums_without_partner(self, options, expanded_partner=None):
        """Get the sum of lines without partner reconciled with a line with a partner, grouped by partner. Those lines
        should be considered as belonging the partner for the reconciled amount as it may clear some of the partner
        invoice/bill and they have to be accounted in the partner balance."""

        params = []
        if expanded_partner:
            partner_clause = "= %s"
            params = [expanded_partner.id]
        else:
            partner_clause = "IS NOT NULL"

        new_options = self._get_options_without_partner(options)
        params = [options["date"]["date_from"]] + params + [options["date"]["date_to"]]
        tables, where_clause, where_params = self._query_get(new_options, domain=[])
        params += where_params
        # custo code start
        query = """
            SELECT
                aml_with_partner.partner_id AS groupby,
                SUM(CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END) AS debit,
                SUM(CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END) AS credit,
                SUM(CASE WHEN aml_with_partner.balance > 0 THEN -partial.amount ELSE partial.amount END) AS balance,
                SUM(account_move_line.amount_currency) AS amount_currency,
                MAX(account_move_line.currency_id) AS currency_id,
                count(distinct account_move_line.currency_id) AS distinct_currencies,
                CASE WHEN partial.max_date < %s THEN 'initial_balance' ELSE 'sum' END as key
            FROM {tables}, account_partial_reconcile partial, account_move_line aml_with_partner
            WHERE (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
               AND account_move_line.partner_id IS NULL
               AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
               AND aml_with_partner.partner_id {partner_clause}
               AND partial.max_date <= %s
               AND {where_clause}
            GROUP BY aml_with_partner.partner_id, key
        """.format(
            tables=tables, partner_clause=partner_clause, where_clause=where_clause
        )
        # custo code ends
        return query, params

    @api.model
    def _do_query(self, options, expanded_partner=None):
        """Execute the queries, perform all the computation and return partners_results,
        a lists of tuple (partner, fetched_values) sorted by the table's model _order:
            - partner is a res.parter record.
            - fetched_values is a dictionary containing:
                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        :param options:             The report options.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :param fetch_lines:         A flag to fetch the account.move.lines or not (the 'lines' key in accounts_values).
        :return:                    (accounts_values, taxes_results)
        """

        def assign_sum(row):
            key = row["key"]
            fields = (
                ["balance", "debit", "credit", "amount_currency", "distinct_currencies", "currency_id"]  # custom field
                if key == "sum"
                else ["balance"]
            )
            if any(not company_currency.is_zero(row[field]) for field in fields):
                groupby_partners.setdefault(row["groupby"], defaultdict(lambda: defaultdict(float)))
                for field in fields:
                    groupby_partners[row["groupby"]][key][field] += row[field]

        company_currency = self.env.company.currency_id

        # flush the tables that gonna be queried
        self.env["account.move.line"].flush(fnames=self.env["account.move.line"]._fields)
        self.env["account.move"].flush(fnames=self.env["account.move"]._fields)
        self.env["account.partial.reconcile"].flush(fnames=self.env["account.partial.reconcile"]._fields)

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options, expanded_partner=expanded_partner)
        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            assign_sum(res)

        # Fetch the lines of unfolded accounts.
        unfold_all = options.get("unfold_all") or (self._context.get("print_mode") and not options["unfolded_lines"])
        # unfold_all = True
        if expanded_partner or unfold_all or options["unfolded_lines"]:
            query, params = self._get_query_amls(options, expanded_partner=expanded_partner)
            self._cr.execute(query, params)
            for res in self._cr.dictfetchall():
                if res["partner_id"] not in groupby_partners:
                    continue
                groupby_partners[res["partner_id"]].setdefault("lines", [])
                groupby_partners[res["partner_id"]]["lines"].append(res)

            query, params = self._get_lines_without_partner(options, expanded_partner=expanded_partner)
            self._cr.execute(query, params)
            for row in self._cr.dictfetchall():
                # don't show lines of partners not expanded
                if row["partner_id"] in groupby_partners:
                    groupby_partners[row["partner_id"]].setdefault("lines", [])
                    row["class"] = " text-muted"
                    groupby_partners[row["partner_id"]]["lines"].append(row)
                if None in groupby_partners:
                    # reconciled lines without partners are fetched to be displayed under the matched partner
                    # and thus but be inversed to be displayed under the unknown partner
                    none_row = row.copy()
                    none_row["class"] = " text-muted"
                    none_row["debit"] = row["credit"]
                    none_row["credit"] = row["debit"]
                    none_row["balance"] = -row["balance"]
                    none_row["amount_currency"] = row["amount_currency"]  # custo code
                    groupby_partners[None].setdefault("lines", [])
                    groupby_partners[None]["lines"].append(none_row)

        # correct the sums per partner, for the lines without partner reconciled with a line having a partner
        query, params = self._get_sums_without_partner(options, expanded_partner=expanded_partner)
        self._cr.execute(query, params)
        total = total_debit = total_credit = total_initial_balance = total_amount_in_currency = 0  # custo code
        for row in self._cr.dictfetchall():
            key = row["key"]
            total_debit += key == "sum" and row["debit"] or 0
            total_credit += key == "sum" and row["credit"] or 0
            total_amount_in_currency += key == "sum" and row["amount_currency"] or 0  # custo code
            total_initial_balance += key == "initial_balance" and row["balance"] or 0
            total += key == "sum" and row["balance"] or 0
            if None not in groupby_partners and not (expanded_partner or unfold_all or options["unfolded_lines"]):
                groupby_partners.setdefault(None, {})
            if row["groupby"] not in groupby_partners:
                continue
            assign_sum(row)

        if None in groupby_partners:
            if "sum" not in groupby_partners[None]:
                groupby_partners[None].setdefault("sum", {"debit": 0, "credit": 0, "balance": 0, "amount_currency": 0})
            if "initial_balance" not in groupby_partners[None]:
                groupby_partners[None].setdefault("initial_balance", {"balance": 0})
            # debit/credit are inversed for the unknown partner as the computation is made regarding the balance of the known partner
            groupby_partners[None]["sum"]["debit"] += total_credit
            groupby_partners[None]["sum"]["credit"] += total_debit
            groupby_partners[None]["sum"]["balance"] -= total
            groupby_partners[None]["initial_balance"]["balance"] -= total_initial_balance
            groupby_partners[None]["sum"]["amount_currency"] += total_amount_in_currency  # custo code

        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # Note a search is done instead of a browse to preserve the table ordering.
        if expanded_partner:
            partners = expanded_partner
        elif groupby_partners:
            partners = (
                self.env["res.partner"]
                .with_context(active_test=False)
                .search([("id", "in", list(groupby_partners.keys()))])
            )
        else:
            partners = []

        # Add 'Partner Unknown' if needed
        if None in groupby_partners.keys():
            partners = [p for p in partners] + [None]
        return [(partner, groupby_partners[partner.id if partner else None]) for partner in partners]

    ####################################################
    # COLUMNS/LINES
    ####################################################

    @api.model
    def _get_report_line_partner(
        self, options, partner, initial_balance, debit, credit, balance, amount_currency, currency_set
    ):
        company_currency = self.env.company.currency_id
        unfold_all = self._context.get("print_mode") and not options.get("unfolded_lines")

        currency_list = list(currency_set)
        columns = [
            {"name": self.format_value(initial_balance), "class": "number"},
            {"name": self.format_value(debit), "class": "number"},
            {"name": self.format_value(credit), "class": "number"},
        ]
        if self.user_has_groups("base.group_multi_currency"):
            if currency_list and len(currency_list) == 1:
                currency = self.env["res.currency"].browse(currency_list[0])  # custo
                columns.append({"name": self.format_value(amount_currency, currency=currency), "class": "number"})
            else:
                columns.append({"name": ""})
        columns.append({"name": self.format_value(balance), "class": "number"})

        return {
            "id": "partner_%s" % (partner.id if partner else 0),
            "partner_id": partner.id if partner else None,
            "name": partner is not None and (partner.name or "")[:128] or _("Unknown Partner"),
            "columns": columns,
            "level": 2,
            "trust": partner.trust if partner else None,
            "unfoldable": not company_currency.is_zero(debit) or not company_currency.is_zero(credit),
            "unfolded": "partner_%s" % (partner.id if partner else 0) in options["unfolded_lines"] or unfold_all,
            "colspan": 6,
        }

    @api.model
    def _get_report_line_total(self, options, initial_balance, debit, credit, balance, amount_currency, currency_set):
        currency_list = list(currency_set)
        columns = [
            {"name": self.format_value(initial_balance), "class": "number"},
            {"name": self.format_value(debit), "class": "number"},
            {"name": self.format_value(credit), "class": "number"},
        ]
        if self.user_has_groups("base.group_multi_currency"):
            if currency_list and len(currency_list) < 2:
                currency = self.env["res.currency"].browse(currency_list[0])  # custo
                columns.append(
                    {"name": self.format_value(amount_currency, currency=currency), "class": "number"}
                )  # custo
            else:
                columns.append({"name": ""})
        columns.append({"name": self.format_value(balance), "class": "number"})
        return {
            "id": "partner_ledger_total_%s" % self.env.company.id,
            "name": _("Total"),
            "class": "total",
            "level": 1,
            "columns": columns,
            "colspan": 6,
        }

    @api.model
    def _get_partner_ledger_lines(self, options, line_id=None):
        """Get lines for the whole report or for a specific line.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        """
        lines = []
        unfold_all = options.get("unfold_all") or (self._context.get("print_mode") and not options["unfolded_lines"])

        expanded_partner = line_id and self.env["res.partner"].browse(int(line_id[8:]))
        partners_results = self._do_query(options, expanded_partner=expanded_partner)
        total_initial_balance = total_debit = total_credit = total_balance = total_amount_currency = 0.0
        all_currency_set = set()
        for partner, results in partners_results:
            is_unfolded = "partner_%s" % (partner.id if partner else 0) in options["unfolded_lines"]

            # res.partner record line.
            partner_sum = results.get("sum", {})
            partner_init_bal = results.get("initial_balance", {})

            initial_balance = partner_init_bal.get("balance", 0.0)
            debit = partner_sum.get("debit", 0.0)
            credit = partner_sum.get("credit", 0.0)
            amount_currency = partner_sum.get("amount_currency", 0.0)  # custo code
            balance = initial_balance + partner_sum.get("balance", 0.0)
            foreign_currency_id = int(partner_sum.get("currency_id", 0.0))  # custo code
            foreign_currency_count = int(partner_sum.get("distinct_currencies", 0.0))  # custo code

            currency_set = set()
            if foreign_currency_count == 1:
                currency_set.add(foreign_currency_id)
                all_currency_set.add(foreign_currency_id)

            lines.append(
                self._get_report_line_partner(
                    options, partner, initial_balance, debit, credit, balance, amount_currency, currency_set
                )
            )

            total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_balance += balance
            total_amount_currency += amount_currency  # custo code
            if unfold_all or is_unfolded:
                cumulated_balance = initial_balance

                # account.move.line record lines.
                amls = results.get("lines", [])

                load_more_remaining = len(amls)
                load_more_counter = self._context.get("print_mode") and load_more_remaining or self.MAX_LINES

                for aml in amls:
                    # Don't show more line than load_more_counter.
                    if load_more_counter == 0:
                        break

                    cumulated_init_balance = cumulated_balance
                    cumulated_balance += aml["balance"]
                    lines.append(
                        self._get_report_line_move_line(
                            options, partner, aml, cumulated_init_balance, cumulated_balance
                        )
                    )

                    load_more_remaining -= 1
                    load_more_counter -= 1

                if load_more_remaining > 0:
                    # Load more line.
                    lines.append(
                        self._get_report_line_load_more(
                            options,
                            partner,
                            self.MAX_LINES,
                            load_more_remaining,
                            cumulated_balance,
                        )
                    )

        if not line_id:
            # Report total line.
            lines.append(
                self._get_report_line_total(
                    options,
                    total_initial_balance,
                    total_debit,
                    total_credit,
                    total_balance,
                    total_amount_currency,  # custo code
                    all_currency_set,
                )
            )
        return lines
