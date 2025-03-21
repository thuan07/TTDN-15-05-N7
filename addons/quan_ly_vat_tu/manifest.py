{
    'name': "du_an",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'du_an'],
    'data': [
        'security/project_purchase_security.xml',
        'security/ir.model.access.csv',
        'views/project_purchase_request_views.xml',
        'views/project_material_views.xml',
        'views/project_supplier_views.xml',
        'views/project_views.xml',
        'views/purchase_order_views.xml',
        'views/menu_views.xml',
        'wizards/create_purchase_order_views.xml',
        'reports/project_material_report_templates.xml',
        'reports/project_material_report.xml',
    ],
    'demo': [
        'demo/project_purchase_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}