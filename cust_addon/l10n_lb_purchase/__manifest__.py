{
    "name": "Lebanese purchase",
    "description": """
        Lebanon purchase localization
    """,
    "author": "Odoo",
    "website": "https://www.odoo.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["l10n_lb_exchange_rate", "purchase"],
    "data": [
        "views/purchase.xml",
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
