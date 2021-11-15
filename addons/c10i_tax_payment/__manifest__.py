# -*- coding: utf-8 -*-
{
    'name': "c10i_tax_payment",

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
    'depends': ['base','account', 'c10i_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/approval_notification_views.xml',
        # 'views/templates.xml',
        'wizard/create_payment_view.xml',
        'wizard/wizard_report_ppn_views.xml',
        'views/tax_payment.xml',
        'views/tax_payment_line.xml',
        'views/tax_account_group_views.xml',
        'security/tax_payment_security.xml',
        # 'security/tax_payment_security.xml',
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}