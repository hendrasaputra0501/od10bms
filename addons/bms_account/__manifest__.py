# -*- coding: utf-8 -*-
{
    'name'      : "Accounting Module for Bumi Maju Sawit",
    'category'  : 'Accounting',
    'version'   : '1.0.0.1',
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.kosaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['account','base','c10i_account', 'account_asset', 'c10i_account_invoice_advance'],
    'summary'   : """
                        BMS Accouting Module
                    """,
    'description'   : """
                        Customize Modul Accounting BMS
                    """,
    'data': [
        # 'security/ir.model.access.csv',
        'security/account.xml',
        'views/komparasi_wizard.xml',
        'views/komparasi_view.xml',
        'views/account_voucher_views.xml',
        'views/account_asset_views.xml',
        'views/account_invoice_views.xml',
        'views/account_move_views.xml',
        'reports/report_views.xml',
        'wizard/account_financial_report_view.xml',
        'wizard/wizard_neraca_view.xml',
        'wizard/wizard_laba_rugi_view.xml',
    ],

    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
