# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'COA - PT Bumi Maju Sawit',
    'version': '1.0',
    'category': 'Localization',
    'description': """
This is the latest Indonesian Odoo localisation necessary to run Odoo accounting for SME's with:
=================================================================================================

* generic Indonesian chart of accounts
* tax structure
* a few other adaptations


    """,
    'author': 'konsaltenindonesia.com',
    'website': 'https://konsaltenindonesia.com.com',
    'depends': [ 'base', 'account','account_parent','base_iban', 'base_vat'],
    'data': [
        'data/l10n_id_chart_data.xml',
        'data/account.account.template.csv',
        'data/account.chart.template.csv',
        'data/account.account.tag.csv',
        'data/account.tax.template.csv',
        'data/account_chart_template_data.yml',
    ],
    'demo' : [],
}
