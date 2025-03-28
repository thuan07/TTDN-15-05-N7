# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'WMS Accounting',
    'version': '1.1',
    'summary': 'Inventory, Logistic, Valuation, Accounting',
    'description': """
WMS Accounting module
======================
This module makes the link between the 'stock' and 'account' modules and allows you to create accounting entries to value your stock movements

Key Features
------------
* Stock Valuation (periodical or automatic)
* Invoice from Picking

Dashboard / Reports for Warehouse Management includes:
------------------------------------------------------
* Stock Inventory Value at given date (support dates in the past)
    """,
    'depends': ['stock', 'account'],
    'category': 'Hidden',
    'sequence': 16,
    'data': [
        'security/stock_account_security.xml',
        'security/ir.model.access.csv',
        'data/stock_account_data.xml',
        'views/stock_account_views.xml',
        'views/res_config_settings_views.xml',
        'data/product_data.xml',
        'views/product_views.xml',
        'views/stock_quant_views.xml',
        'views/report_invoice.xml',
        'views/stock_valuation_layer_views.xml',
        'wizard/stock_request_count.xml',
        'wizard/stock_valuation_layer_revaluation_views.xml',
        'report/report_stock_forecasted.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': True,
    'post_init_hook': '_configure_journals',
    'license': 'LGPL-3',
}
