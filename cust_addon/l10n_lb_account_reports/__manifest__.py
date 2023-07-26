{
    "name": "accounting_reports_currency",
    "summary": """
        Enables multi-currency reporting for some accounting reports""",
    "author": "Odoo PS",
    "website": "https://www.odoo.com",
    "license": "OEEL-1",
    "category": "Accounting",
    "version": "15.0.1.0.0",
    "depends": ["account_reports", "l10n_lb_exchange_rate"],
    "data": [
        "views/views.xml",
        "views/res_company.xml",
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
