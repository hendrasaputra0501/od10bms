# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia <www.konsaltenindonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################
{
    'name'      : "Stock Issue",
    'category'  : 'Custom Module',
    'version'   : '1.0.0.1',
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.konsaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base', 'c10i_base',
                   'stock', 'c10i_stock', 
                   'c10i_account', 'c10i_account_location',
                   'c10i_stock_inter_warehouse'],
    'summary'   : """ Sometimes Consuming Products need to have spesific Account Allocation""",
    'description'   : """ """,
    'data'      : [
        'reports/report_views.xml',
        'views/stock_picking_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
}
