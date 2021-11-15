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
    'name'      : 'Stock Average Cost Price per Stock Location',
    'version'   : '1.0.1.1',
    'category'  : 'Inventory Management',
    'description': "-",
    'summary'   : """
                    Inventory Management Module modified by Consult10 Indonesia to localization use in Indonesia
                    """,
    'author'    : "Konsaltén Indonesia",
    'website'   : "www.konsaltenindonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base','stock_account', 'purchase', 'c10i_stock', 'c10i_stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
