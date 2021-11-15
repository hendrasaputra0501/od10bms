# -*- coding: utf-8 -*-
{
    'name': "bms_purchase",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'bms_base', 'c10i_purchase_request', 'purchase', 'c10i_purchase'],

    # always loaded
    'data': [
        'security/purchase_security.xml',
        'security/ir.model.access.csv',
        'views/purchase_request_views.xml',
        'views/purchase_rfq.xml',
        'views/purchase_order.xml',
        'reports/report_views.xml',
    ],
}