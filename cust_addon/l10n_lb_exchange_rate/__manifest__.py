{
    "name": "Lebanon accounting localization",
    "description": """
        Lebanon accounting localization
    """,
    "author": "Odoo",
    "website": "https://www.odoo.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["base", "account"],
    "data": [
        "data/res_currency.xml",
        "views/account_move.xml",
        "views/res_company.xml",
        "views/account_payment.xml",
        "wizard/account_payment_register.xml",
    ],
    'license': 'LGPL-3',
}
