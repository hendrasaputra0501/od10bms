# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2020  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Hendra Saputra <hendrasaputra0501@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

{
    'name'      : 'Intra Warehouse Transfer',
    'version'   : '1.0.1.1',
    'category'  : 'Inventory Management',
    'description': "-",
    'summary'   : """ """,
    'author'    : "Konsaltén Indonesia (Consult10 Indonesia)",
    'website'   : "www.consult10indonesia.com",
    'license'   : 'AGPL-3',
    'depends'   : ['base', 'c10i_base', 'c10i_stock', 'c10i_stock_account', 'c10i_stock_price_loc'],
    'data': [
        'views/product_view.xml',
        'views/stock_picking_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}