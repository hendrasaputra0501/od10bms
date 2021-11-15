# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Anggar Bagus Kurniawan <anggar.bagus@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

{
    'name'      : "LHP Module for PT. Bumi Maju Sawit",
    'category'  : 'Custom Module',
    'version'   : '1.0.0.1',
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.konsaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base', 'c10i_base', 'bms_base', 'stock', 'c10i_stock', 'c10i_account', 'c10i_account_location','c10i_palm_oil_mill'],
    'summary'   : """
                        BMS LHP Module - C10i
                    """,
    'description'   : """
Customize Modul Base BMS
========================

Preferences
-----------
* Add LHP, SOUNDING
                    """,
    'data'      : [
        'views/mill_storage_views.xml',
        'views/mill_density_chart_views.xml',
        'views/mill_daily_sounding_view.xml',
        'views/mill_lhp_view.xml',
        'views/mill_valuation_bms_views.xml',
        'views/mill_lhp_type_views.xml',
        'report/report_lhp_qweb.xml',
        'data/lhp_digit_precision.xml',
        'data/uom.xml',
        'report/report_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
