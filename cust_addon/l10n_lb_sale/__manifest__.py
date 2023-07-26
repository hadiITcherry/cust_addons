{
    "name": "Lebanese sales",
    "description": """
        Lebanon sales localization
    """,
    "author": "Odoo",
    "website": "https://www.odoo.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["l10n_lb_exchange_rate", "sale"],
    "data": [
        "views/sale.xml",
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
